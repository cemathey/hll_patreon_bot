import asyncio
import os
import sys
from pathlib import Path

import discord

from ..database.models import engine
from .constants import (
    API_KEY_FORMAT,
    CRCON_API_KEY,
    CRCON_URL,
    DISCORD_ADMIN_ROLE_IDS,
    DISCORD_BOT_TOKEN,
    DISCORD_GUILD_ID,
    PATREON_ACCESS_TOKEN,
    PATREON_CAMPAIGN_ID,
    PATREON_HOST_NAME,
)

mandatory_variables = {
    "CRCON_API_KEY": CRCON_API_KEY,
    "DISCORD_BOT_TOKEN": DISCORD_BOT_TOKEN,
    "DISCORD_GUILD_ID": DISCORD_GUILD_ID,
    "CRCON_URL": CRCON_URL,
    "DISCORD_ADMIN_ROLE_IDS": DISCORD_ADMIN_ROLE_IDS,
    "PATREON_HOST_NAME": PATREON_HOST_NAME,
    "PATREON_ACCESS_TOKEN": PATREON_ACCESS_TOKEN,
    "PATREON_CAMPAIGN_ID": PATREON_CAMPAIGN_ID,
}

for var, value in mandatory_variables.items():
    if not value:
        print(f"{var} not set")
        sys.exit(1)


intents = discord.Intents.all()
intents.message_content = True

bot = discord.Bot(intents=intents)

# bot.load_extensions("cogs.crcon", "cogs.patreon", "cogs.user", package="..")
# bot.load_extension("cogs.crcon")
# bot.load_extension(".cogs.crcon", package="hll_patreon_bot")


def load_all_cogs():
    path = os.getenv("PYTHON_PATH")
    # print(f"{path=}")
    for cog in os.listdir(Path("./hll_patreon_bot/bot/cogs")):
        if cog.endswith(".py"):
            try:
                cog = f"hll_patreon_bot.bot.cogs.{cog.replace('.py', '')}"
                print(f"Loading {cog=}")
                bot.load_extension(cog)
            except Exception as e:
                print(f"{cog} can not be loaded:")
                raise e
    print("Loaded all cogs")


headers = {"Authorization": API_KEY_FORMAT.format(api_key=CRCON_API_KEY)}


# @bot.listen()
# async def on_connect():
#     # if bot.auto_sync_commands:
#     await bot.sync_commands(force=True)
#     print(f"{bot.user.name} connected.")


@bot.listen()
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")  # type: ignore
    print("------")


async def main():
    pass


if __name__ == "__main__":
    asyncio.run(main())
    load_all_cogs()
    bot.run(DISCORD_BOT_TOKEN)
