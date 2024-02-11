from datetime import datetime, timezone
from logging import getLogger
from pprint import pprint

import discord
import httpx
from bot.constants import API_KEY_FORMAT, CRCON_API_KEY, CRCON_URL, PATREON_HOST_NAME
from bot.integrations import crcon
from bot.models import enter_session
from bot.types import PlayerProfileType
from bot.utils import (
    get_set_crcon_record,
    get_set_discord_record,
    link_primary_crcon_to_discord,
    link_sponsored_crcon_to_discord,
    one_or_none,
    raise_on_4xx_5xx,
    unlink_primary_crcon_from_discord,
    user_as_unique_name,
    with_permission,
)
from discord.commands import ApplicationContext
from discord.ext import commands
from patreon_v2 import typedefs as patreon_api_types
from patreon_v2.async_api import AsyncAPI as PatreonAPI
from sqlalchemy import select

logger = getLogger(__name__)


def create_crcon_embed(player: PlayerProfileType) -> discord.Embed:
    embed = discord.Embed()

    embed.add_field(name="Player ID", value=player["steam_id_64"])
    embed.add_field(
        name="Name:", value=player["names"][0]["name"] if player["names"] else ""
    )
    akas = ", ".join(p["name"] for p in player["names"][1:])
    embed.add_field(name="AKA: ", value=akas)
    if player["vips"]:
        for vip in player["vips"]:
            embed.add_field(
                name=f"VIP Status {vip['server_number']}",
                value=f"<t:{vip['expiration'].timestamp()}:f>",
            )
    embed.timestamp = datetime.now(tz=timezone.utc)

    return embed


class Crcon(commands.Cog):
    def __init__(self, bot, crcon_url: str | None = None) -> None:
        super().__init__()
        self.bot = bot
        self.crcon_url = crcon_url or CRCON_URL

    # TODO make this better
    @property
    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers={"Authorization": API_KEY_FORMAT.format(api_key=CRCON_API_KEY)},
            event_hooks={"response": [raise_on_4xx_5xx]},
        )

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
        # Find discord ID record, make if none
        # Check CRCON for player ID existence, reject if not found unless forced
        # Find player record, make if none
        # Link them together
        if not with_permission(ctx):
            return

        try:
            crcon_record = await crcon.fetch_player(
                client=self.client, rcon_url=CRCON_URL, player_id=player_id
            )
        except httpx.HTTPError as e:
            logger.error(e)
            await ctx.respond(e)
            crcon_record = None

        pprint(crcon_record)

        if not crcon_record and not force:
            await ctx.respond(
                f"No player found in CRCON for player_id=`{player_id}`, double check the player ID and reattempt with `force` set to True if you're sure."
            )
            return

        player_id_already_linked = False
        previous_linked_discord = None
        with enter_session() as session:
            (
                player_id_already_linked,
                previous_linked_discord,
            ) = link_primary_crcon_to_discord(
                session=session, player_id=player_id, discord_name=discord_user.name
            )

        if player_id_already_linked:
            await ctx.respond(
                f"Linked {discord_user} to {player_id=} (was previously linked to {previous_linked_discord})"
            )
        else:
            await ctx.respond(f"Linked {discord_user} to {player_id=}")

    @discord.slash_command(description="")
    async def unlink_primary_crcon(
        self, ctx: ApplicationContext, discord_user: discord.User
    ):
        if not with_permission(ctx):
            return

        with enter_session() as session:
            deleted_player_ids = unlink_primary_crcon_from_discord(
                session=session, discord_name=discord_user.name
            )

        # TODO: include main/sponsored status
        await ctx.respond(
            f"Unlinked {discord_user} from {','.join(deleted_player_ids)}"
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
        try:
            crcon_record = await crcon.fetch_player(
                client=self.client, rcon_url=CRCON_URL, player_id=player_id
            )
        except httpx.HTTPError as e:
            logger.error(e)
            await ctx.respond(e)
            crcon_record = None

        pprint(crcon_record)
        # print(f"crcon_record = {crcon_record['steam_id_64'] if crcon_record else None}")

        if not crcon_record and not force:
            await ctx.respond(
                f"No player found in CRCON for player_id=`{player_id}`, double check the player ID and reattempt with `force` set to True if you're sure."
            )
            return

        with enter_session() as session:
            (
                player_id_already_linked,
                previous_linked_discord,
            ) = link_sponsored_crcon_to_discord(
                session=session, discord_name=discord_user.name, player_id=player_id
            )

        if player_id_already_linked:
            await ctx.respond(
                f"Linked {player_id} to {discord_user} (was previously linked to {previous_linked_discord})"
            )
        else:
            await ctx.respond(f"Linked {player_id} to {discord_user}")

    @discord.slash_command(description="Add VIP to the given discord account")
    async def add_vip(
        self,
        ctx: ApplicationContext,
        discord_user: discord.User,
        expiration: str | None,
    ):
        # Look up the CRCON player ID or fail
        # Look up the discord ID
        # Get the name automatically
        pass

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
            await ctx.respond(embed=create_crcon_embed(player))
        else:
            await ctx.respond(f"{player_id} not found")


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Crcon(bot))  # add the cog to the bot
