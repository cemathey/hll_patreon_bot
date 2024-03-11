import json
import urllib
from datetime import datetime
from pprint import pprint
from typing import Any
from urllib.parse import urljoin

import httpx
from loguru import logger

from hll_patreon_bot.bot.constants import (
    CRCON_SERVER_NUMBER,
    CRCON_URL,
    MISSING_PLAYER_NAME,
)
from hll_patreon_bot.bot.utils import one_or_none
from hll_patreon_bot.integrations.crcon.types import (
    PlayerProfileType,
    PlayerVIPType,
    RconAPIResponse,
    VipPlayer,
)


async def add_vip(
    client: httpx.AsyncClient,
    player_id: str,
    name: str,
    expiration_timestamp: datetime,
    server_url: str = CRCON_URL,
    endpoint: str = "do_add_vip",
) -> RconAPIResponse:
    url = urljoin(server_url, endpoint)

    payload = {
        "steam_id_64": player_id,
        "name": name,
        "expiration": expiration_timestamp,
    }

    logger.info(
        f"Adding/updating VIP expiration for {player_id=} {name=} {expiration_timestamp=}"
    )
    res = await client.post(url=url, data=payload)
    res_body: RconAPIResponse = res.json()
    return res_body


async def remove_vip(
    client: httpx.AsyncClient,
    player_id: str,
    server_url: str = CRCON_URL,
    endpoint: str = "do_remove_vip",
):
    url = urljoin(server_url, endpoint)
    payload = {
        "steam_id_64": player_id,
    }

    res = await client.post(url=url, data=payload)
    res_body: RconAPIResponse = res.json()
    return res_body


async def add_flag(
    client: httpx.AsyncClient,
    player_id: str,
    flag: str,
    comment: str | None = None,
    server_url: str = CRCON_URL,
    endpoint: str = "flag_player",
):
    url = urljoin(server_url, endpoint)
    payload = {"steam_id_64": player_id, "flag": flag, "comment": comment}

    res = await client.post(url=url, data=payload)
    # res.raise_for_status()
    res_body: RconAPIResponse = res.json()
    return res_body


async def remove_flag(
    client: httpx.AsyncClient,
    # player_id: str,
    flag_id: int,
    server_url: str = CRCON_URL,
    endpoint: str = "unflag_player",
):
    url = urljoin(server_url, endpoint)
    # TODO: need to add other methods to find the flag ID
    # or possibly update CRCON to improve the endpoint
    payload = {"flag_id": flag_id}

    res = await client.post(url=url, data=payload)
    res_body: RconAPIResponse = res.json()
    return res_body


# TODO: handle backoff/retry
async def fetch_current_vips(
    client: httpx.AsyncClient,
    server_url: str = CRCON_URL,
    endpoint="api/get_vip_ids",
) -> dict[str, VipPlayer]:
    url = urljoin(server_url, endpoint)
    response = await client.get(url=url)

    raw_vips = response.json()["result"]
    return {
        vip["steam_id_64"]: VipPlayer(
            steam_id_64=vip["steam_id_64"],
            name=vip["name"],
            expiration_date=vip["vip_expiration"],
        )
        for vip in raw_vips
    }


async def fetch_player(
    client: httpx.AsyncClient,
    player_id: str,
    rcon_url: str = CRCON_URL,
    endpoint: str = "api/player",
) -> PlayerProfileType | None:
    params = {"steam_id_64": player_id}
    url = urljoin(rcon_url, endpoint)
    res = await client.get(url=url, params=params)

    res_body: RconAPIResponse = res.json()
    return res_body["result"]


async def fetch_current_expiration(
    client: httpx.AsyncClient,
    player_id: str,
    server_number: int = CRCON_SERVER_NUMBER,
) -> PlayerVIPType | None:
    profile = await fetch_player(client=client, player_id=player_id)

    if profile:
        vip_info = one_or_none(
            lambda p: p["server_number"] == server_number, profile["vips"]
        )
        if vip_info and profile["names"] and len(profile["names"]) > 0:
            vip_info["vip_name"] = profile["names"][0]["name"]
        elif vip_info:
            vip_info["vip_name"] = MISSING_PLAYER_NAME

        return vip_info
