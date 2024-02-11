import os
import urllib.parse
from datetime import datetime, timedelta, timezone

COMMAND_PREFIX = "/"
API_KEY_FORMAT = "Bearer: {api_key}"
AUTH_HEADER = "Authorization"

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
CRCON_API_KEY = os.getenv("CRCON_API_KEY", "")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID", "")
CRCON_URL = os.getenv("CRCON_URL", "")
if not CRCON_URL.endswith("api"):
    CRCON_URL = urllib.parse.urljoin(CRCON_URL, "api")

CRCON_SERVER_NUMBER = int(os.getenv("CRCON_SERVER_NUMBER", 1))

DISCORD_ADMIN_ROLE_IDS = os.getenv("DISCORD_ADMIN_ROLE_IDS", "")
AUTHORIZED_DISCORD_ROLES = DISCORD_ADMIN_ROLE_IDS.split(",")

PATREON_ACCESS_TOKEN = os.getenv("PATREON_ACCESS_TOKEN", "")
PATREON_HOST_NAME = os.getenv("PATREON_HOST_NAME", "")
PATREON_CAMPAIGN_ID = os.getenv("PATREON_CAMPAIGN_ID", "")

CRCON_SUCCESS = "SUCCESS"

# TODO: expose this as a configurable option
CRCON_VIP_NAME_FORMAT = "{name} | {email} | HLLPatreonBot"

PATREON_REWARD_TIMEDELTA = timedelta(days=30)

MISSING_PLAYER_NAME = "No player name"
