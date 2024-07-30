from functools import cached_property

import discord
import httpx
from discord.commands import ApplicationContext
from discord.ext import commands
from loguru import logger

from hll_patreon_bot.bot.cogs.crcon import create_crcon_player_embed
from hll_patreon_bot.bot.constants import (
    API_KEY_FORMAT,
    CRCON_API_KEY,
    EMPTY_EMBED_FIELD,
)
from hll_patreon_bot.bot.utils import (
    add_blank_embed_field,
    discord_name_as_user,
    raise_on_4xx_5xx,
    with_permission,
)
from hll_patreon_bot.database.models import DiscordPlayers, enter_session
from hll_patreon_bot.database.utils import get_set_discord_record
from hll_patreon_bot.integrations.crcon import crcon
from hll_patreon_bot.integrations.crcon.crcon import fetch_players
from hll_patreon_bot.integrations.crcon.types import PlayerProfileType, ServerDetails


def create_status_embed(
    patreon_id: str | None,
    discord_name: str,
    players: list[DiscordPlayers],
    player_profiles: dict[str, PlayerProfileType],
    guild_members: list[discord.Member],
    own_status: bool = False,
) -> discord.Embed:
    embed = discord.Embed()
    embed.title = "Your Status" if own_status else "Status"
    embed.add_field(name="Patreon ID", value=str(patreon_id), inline=False)

    discord_user = discord_name_as_user(
        discord_name=discord_name, members=guild_members
    )
    if not own_status:
        embed.add_field(name="Discord", value=discord_user.mention, inline=False)

    for p in [p for p in players if p.main]:
        embed.add_field(
            name="Your Player ID" if own_status else "Primary Player ID",
            value=p.player.player_id,
            inline=False,
        )
        embed.add_field(
            name="Your Player Name" if own_status else "Primary Player Name",
            value=player_profiles[p.player.player_id]["names"][0]["name"],
            inline=False,
        )
        # TODO: Include expiration dates somehow

    add_blank_embed_field(embed=embed)

    embed.add_field(name="Sponsored Players:", value=EMPTY_EMBED_FIELD, inline=False)
    for p in [p for p in players if not p.main]:
        sponsored_discord_name: DiscordPlayers | None = None
        try:
            for sp in p.player.discords:
                if sp.player_id == p.player_id:
                    sponsored_discord_name = sp
        except IndexError:
            sponsored_discord_name = None
        embed.add_field(
            name="Discord",
            value=discord_name_as_user(
                discord_name=sponsored_discord_name.discord.discord_name,
                members=guild_members,
            ).mention,
        )
        embed.add_field(
            name="Player ID",
            value=p.player.player_id,
            inline=True,
        )
        embed.add_field(
            name="Player Name",
            value=player_profiles[p.player.player_id]["names"][0]["name"],
            inline=False,
        )

    return embed


class User(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot

    @cached_property
    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers={"Authorization": API_KEY_FORMAT.format(api_key=CRCON_API_KEY)},
            event_hooks={"response": [raise_on_4xx_5xx]},
        )

    @property
    async def server_details(self) -> dict[str, ServerDetails]:
        return await crcon.fetch_server_details(self.client)

    @discord.slash_command(description="")
    async def status(self, ctx: ApplicationContext, discord_user: discord.User):
        if not with_permission(ctx):
            return

        await ctx.defer()

        player_embeds = []
        with enter_session() as sess:
            discord_record = get_set_discord_record(
                session=sess, discord_user_name=discord_user.name
            )
            if discord_record:
                player_crcon_records = await fetch_players(
                    client=self.client,
                    player_ids=[p.player.player_id for p in discord_record.players],
                )
                embed = create_status_embed(
                    patreon_id=(
                        discord_record.patreon.patreon_id
                        if discord_record.patreon
                        else None
                    ),
                    discord_name=discord_record.discord_name,
                    players=discord_record.players,
                    player_profiles=player_crcon_records,
                    guild_members=ctx.guild.members if ctx.guild else [],
                    own_status=False,
                )
                player_embeds = [
                    create_crcon_player_embed(
                        player=player, server_details=await self.server_details
                    )
                    for player in player_crcon_records.values()
                ]

                if player_embeds:
                    embeds = [embed, *player_embeds]
                else:
                    embeds = [embed]

                await ctx.respond(embeds=embeds)
            else:
                await ctx.respond(f"No player record found")

    @discord.slash_command(description="")
    async def my_status(self, ctx: ApplicationContext):
        await ctx.defer()

        discord_user = ctx.interaction.user
        with enter_session() as sess:
            discord_record = get_set_discord_record(
                session=sess, discord_user_name=discord_user.name
            )

            # TODO: sort players, format better for main/sponsored
            if discord_record:
                player_crcon_records = await fetch_players(
                    client=self.client,
                    player_ids=[p.player.player_id for p in discord_record.players],
                )
                embed = create_status_embed(
                    patreon_id=(
                        discord_record.patreon.patreon_id
                        if discord_record.patreon
                        else None
                    ),
                    discord_name=discord_record.discord_name,
                    players=discord_record.players,
                    player_profiles=player_crcon_records,
                    guild_members=ctx.guild.members if ctx.guild else [],
                    own_status=True,
                )
                player_embeds = [
                    create_crcon_player_embed(
                        player=player, server_details=await self.server_details
                    )
                    for player in player_crcon_records.values()
                ]
                if player_embeds:
                    embeds = [embed, *player_embeds]
                else:
                    embeds = [embed]

                await ctx.respond(embeds=embeds)
            else:
                await ctx.send(f"No player record found, please open a ticket")


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(User(bot))  # add the cog to the bot
