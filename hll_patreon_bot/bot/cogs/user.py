from datetime import datetime
from pprint import pprint

import discord
import httpx
from discord.commands import ApplicationContext
from discord.ext import commands
from patreon_v2 import typedefs as patreon_api_types
from patreon_v2.async_api import AsyncAPI as PatreonAPI
from sqlalchemy import select

from hll_patreon_bot.bot.constants import CRCON_URL, PATREON_HOST_NAME
from hll_patreon_bot.database.models import Discord, Patreon, Player, enter_session
from hll_patreon_bot.database.utils import get_set_discord_record
from hll_patreon_bot.integrations import crcon
from hll_patreon_bot.integrations.crcon.types import PlayerProfileType


class User(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot

    @discord.slash_command(description="")
    async def status(self, ctx: ApplicationContext, discord_user: discord.User):
        pass

    @discord.slash_command(description="")
    async def my_status(self, ctx: ApplicationContext):
        discord_user = ctx.author
        with enter_session() as sess:
            res = get_set_discord_record(
                session=sess, discord_user_name=discord_user.name
            )

            # TODO: sort players, format better for main/sponsored
            if res:
                patreon_id = res.patreon.patreon_id if res.patreon else None
                players = [str(p) for p in res.players]
                await ctx.respond(f"Patreon ID: {patreon_id} Players: {players}")
            else:
                await ctx.respond(f"No player record found, please open a ticket")

    @discord.slash_command(description="")
    async def search_ids(
        self,
        ctx: ApplicationContext,
        discord_user: discord.User | None,
        patreon_id: str | None,
        player_id: str | None,
    ):
        pass


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(User(bot))  # add the cog to the bot
