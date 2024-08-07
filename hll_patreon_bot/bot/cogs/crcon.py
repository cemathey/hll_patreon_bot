from datetime import datetime, timezone
from functools import cached_property
from pprint import pprint

import discord
import httpx
from discord.commands import ApplicationContext
from discord.ext import commands
from loguru import logger

from hll_patreon_bot.bot.constants import API_KEY_FORMAT, CRCON_API_KEY, CRCON_URL
from hll_patreon_bot.bot.utils import (
    discord_name_as_user,
    raise_on_4xx_5xx,
    with_permission,
)
from hll_patreon_bot.database.models import enter_session
from hll_patreon_bot.database.utils import (
    get_primary_crcon_record,
    get_set_discord_record,
    link_primary_crcon_to_discord,
    link_sponsored_crcon_to_discord,
    unlink_primary_crcon_from_discord,
)
from hll_patreon_bot.integrations.crcon import crcon
from hll_patreon_bot.integrations.crcon.types import PlayerProfileType, ServerDetails


def create_crcon_player_embed(
    player: PlayerProfileType, server_details: dict[str, ServerDetails]
) -> discord.Embed:
    embed = discord.Embed()
    embed.title = "CRCON Player Record"
    embed.add_field(name="Player ID", value=player["player_id"])
    embed.add_field(
        name="Name:", value=player["names"][0]["name"] if player["names"] else ""
    )
    akas = ", ".join(p["name"] for p in player["names"][1:])
    embed.add_field(name="AKA: ", value=akas)
    if player["vips"]:
        for vip in player["vips"]:
            server = server_details.get(str(vip["server_number"]), {})
            if server:
                embed.add_field(
                    name=f"VIP Status Server: {server.get('name')}",
                    value=f"Expires <t:{int(datetime.fromisoformat(vip['expiration']).timestamp())}:f>",
                    inline=False,
                )
    embed.timestamp = datetime.now(tz=timezone.utc)

    return embed


async def _fetch_crcon_player_record(
    ctx: ApplicationContext, client: httpx.AsyncClient, player_id: str
) -> PlayerProfileType | None:
    try:
        crcon_record = await crcon.fetch_player(
            client=client, rcon_url=CRCON_URL, player_id=player_id
        )
    except httpx.HTTPError as e:
        logger.error(e)
        await ctx.respond(f"Unexpected error while fetching player record{e}")
        crcon_record = None
    return crcon_record


class Crcon(commands.Cog):
    def __init__(self, bot, crcon_url: str | None = None) -> None:
        super().__init__()
        self.bot = bot
        self.crcon_url = crcon_url or CRCON_URL

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
    async def link_primary_crcon(
        self,
        ctx: ApplicationContext,
        discord_user: discord.User,
        player_id: str,
        force: bool = False,
        # use this instead of force
        # https://docs.pycord.dev/en/stable/api/clients.html#discord.Bot.wait_for
    ):
        if not with_permission(ctx):
            return

        await ctx.defer()

        player_embed: discord.Embed | None = None
        crcon_record = await _fetch_crcon_player_record(
            ctx=ctx, client=self.client, player_id=player_id
        )
        if crcon_record:
            player_embed = create_crcon_player_embed(
                crcon_record, server_details=await self.server_details
            )

        # logger.debug(f"link_primary_crcon {crcon_record=}")
        embed = discord.Embed()
        if not crcon_record and not force:
            embed.description = f"No player found in CRCON for Player ID `{player_id}`, double check the player ID and reattempt with `force` set to **True** if you're sure."
            await ctx.respond(embed=embed)
            return

        previous_linked_discord = None
        with enter_session() as session:
            previous_linked_discord = link_primary_crcon_to_discord(
                session=session, player_id=player_id, discord_name=discord_user.name
            )

        embed.title = "Primary"
        embed.add_field(name="Player ID", value=player_id)
        embed.description = f"Linked {discord_user.mention}"
        if previous_linked_discord:
            prev_user = discord_name_as_user(
                previous_linked_discord, members=ctx.guild.members
            )
            embed.add_field(name="Previous Linked Discord", value=prev_user.mention)

        if player_embed:
            embeds = [embed, player_embed]
        else:
            embeds = [embed]

        await ctx.respond(embeds=embeds)

    @discord.slash_command(description="")
    async def unlink_primary_crcon(
        self, ctx: ApplicationContext, discord_user: discord.User
    ):
        if not with_permission(ctx):
            return

        with enter_session() as session:
            deleted_player_id = unlink_primary_crcon_from_discord(
                session=session, discord_name=discord_user.name
            )

        if not deleted_player_id:
            # TODO: error message
            await ctx.respond(
                f"{discord_user.mention} was not linked to a CRCON account"
            )
            return

        player_embed: discord.Embed | None = None
        crcon_record = await _fetch_crcon_player_record(
            ctx=ctx, client=self.client, player_id=deleted_player_id
        )
        if crcon_record:
            player_embed = create_crcon_player_embed(
                crcon_record, server_details=await self.server_details
            )

        # TODO: include main/sponsored status
        await ctx.respond(
            f"Unlinked {discord_user.mention} from `{deleted_player_id}",
            embed=player_embed,
        )

    @discord.slash_command(description="")
    async def link_sponsored_crcon(
        self,
        ctx: ApplicationContext,
        discord_user: discord.User,
        player_id: str,
        force: bool = False,
        # use this instead of force
        # https://docs.pycord.dev/en/stable/api/clients.html#discord.Bot.wait_for
    ):
        if not with_permission(ctx):
            return

        await ctx.defer()

        player_embed: discord.Embed | None = None
        crcon_record = await _fetch_crcon_player_record(
            ctx=ctx, client=self.client, player_id=player_id
        )
        logger.info(f"{player_id=} {crcon_record=}")
        if crcon_record:
            player_embed = create_crcon_player_embed(
                crcon_record, server_details=await self.server_details
            )

        embed = discord.Embed()
        embed.title = "Link Sponsored CRCON Player ID"
        if not crcon_record and not force:
            embed.description = f"No player found in CRCON for Player ID `{player_id}`, double check the player ID and reattempt with `force` set to **True** if you're sure."
            await ctx.respond(embed=embed)
            return

        with enter_session() as session:
            previous_linked_discord = link_sponsored_crcon_to_discord(
                session=session, discord_name=discord_user.name, player_id=player_id
            )

        embed.description = f"Player ID `{player_id}` Linked to {discord_user.mention}"
        if previous_linked_discord:
            prev_user = discord_name_as_user(
                previous_linked_discord, members=ctx.guild.members
            )
            embed.add_field(name="Previous Linked Discord", value=prev_user.mention)

        if player_embed:
            embeds = [embed, player_embed]
        else:
            embeds = [embed]

        await ctx.respond(embeds=embeds)

    @discord.slash_command(
        description="Set the primary CRCON accounts VIP expiration based on their Patreon status"
    )
    async def sync_vip_status(
        self, ctx: ApplicationContext, discord_user: discord.User
    ):
        if not with_permission(ctx):
            return

        with enter_session() as session:
            discord_record = get_set_discord_record(
                session=session, discord_user_name=discord_user.name
            )
            player_record = get_primary_crcon_record(
                session=session, discord_user_name=discord_user.name
            )

            if player_record:
                pass

            else:
                await ctx.respond(
                    f"{discord_user} does not have a primary CRCON account linked"
                )

    @discord.slash_command(description="Add VIP to the given discord account")
    async def add_vip(
        self,
        ctx: ApplicationContext,
        discord_user: discord.User,
        description: str,
        expiration: str | None,
    ):
        # TODO finish this

        # Look up the CRCON player ID or fail
        # Look up the discord ID
        # Get the name automatically
        if not with_permission(ctx):
            return

    @discord.slash_command(description="Remove VIP from the given discord account")
    async def remove_vip(self, ctx: ApplicationContext, discord_user: discord.User):
        pass

    @discord.slash_command(
        description="Search CRCON for the specified player (steam/win store) ID"
    )
    async def query_player(self, ctx: ApplicationContext, player_id: str):
        await ctx.respond(f"Searching CRCON for {player_id=}")
        player = await crcon.fetch_player(
            client=self.client,
            rcon_url=self.crcon_url,
            player_id=player_id,
        )

        if player:
            await ctx.respond(
                embed=create_crcon_player_embed(
                    player, server_details=await self.server_details
                )
            )
        else:
            await ctx.respond(f"{player_id} not found")


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Crcon(bot))  # add the cog to the bot
