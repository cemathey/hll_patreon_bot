from functools import cached_property

import discord
import httpx
from discord.commands import ApplicationContext
from discord.ext import commands

from hll_patreon_bot.bot.constants import (
    API_KEY_FORMAT,
    CRCON_API_KEY,
    EMPTY_EMBED_FIELD,
)
from hll_patreon_bot.bot.utils import (
    add_blank_embed_field,
    discord_name_as_user,
    raise_on_4xx_5xx,
)
from hll_patreon_bot.database.models import DiscordPlayers, enter_session
from hll_patreon_bot.database.utils import get_set_discord_record
from hll_patreon_bot.integrations.crcon.crcon import fetch_players
from hll_patreon_bot.integrations.crcon.types import PlayerProfileType


def create_status_embed(
    patreon_id: str | None,
    discord_name: str,
    players: list[DiscordPlayers],
    player_names: dict[str, PlayerProfileType],
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
        # TODO: make an API call to get the player name
        embed.add_field(
            name="Your Player ID" if own_status else "Primary Player ID",
            value=p.player.player_id,
            inline=False,
        )
        embed.add_field(
            name="Your Player Name" if own_status else "Primary Player Name",
            value=player_names[p.player.player_id]["names"][0]["name"],
            inline=False,
        )

    add_blank_embed_field(embed=embed)

    embed.add_field(name="Sponsored Players:", value=EMPTY_EMBED_FIELD, inline=False)
    for p in [p for p in players if not p.main]:
        embed.add_field(
            name="Player ID",
            value=p.player.player_id,
            inline=True,
        )
        embed.add_field(
            name="Player Name",
            value=player_names[p.player.player_id]["names"][0]["name"],
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

    @discord.slash_command(description="")
    async def status(self, ctx: ApplicationContext, discord_user: discord.User):
        with enter_session() as sess:
            res = get_set_discord_record(
                session=sess, discord_user_name=discord_user.name
            )
            if res:
                player_names = await fetch_players(
                    client=self.client,
                    player_ids=[p.player.player_id for p in res.players],
                )
                embed = create_status_embed(
                    patreon_id=res.patreon.patreon_id if res.patreon else None,
                    discord_name=res.discord_name,
                    players=res.players,
                    player_names=player_names,
                    guild_members=ctx.guild.members if ctx.guild else [],
                    own_status=False,
                )
                await ctx.respond(embed=embed)
            else:
                await ctx.respond(f"No player record found")

    @discord.slash_command(description="")
    async def my_status(self, ctx: ApplicationContext):
        discord_user = ctx.interaction.user
        with enter_session() as sess:
            res = get_set_discord_record(
                session=sess, discord_user_name=discord_user.name
            )

            # TODO: sort players, format better for main/sponsored
            if res:
                player_names = await fetch_players(
                    client=self.client,
                    player_ids=[p.player.player_id for p in res.players],
                )
                embed = create_status_embed(
                    patreon_id=res.patreon.patreon_id if res.patreon else None,
                    discord_name=res.discord_name,
                    players=res.players,
                    player_names=player_names,
                    guild_members=ctx.guild.members if ctx.guild else [],
                    own_status=True,
                )
                await ctx.respond(embed=embed)
            else:
                await ctx.send(f"No player record found, please open a ticket")


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(User(bot))  # add the cog to the bot
