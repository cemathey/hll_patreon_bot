import asyncio
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
    ServerDetails,
    VipPlayer,
)


async def add_vip(
    client: httpx.AsyncClient,
    player_id: str,
    description: str,
    expiration_timestamp: datetime,
    server_url: str = CRCON_URL,
    endpoint: str = "add_vip",
) -> RconAPIResponse:
    url = urljoin(server_url, endpoint)

    payload = {
        "player_id": player_id,
        "description": description,
        "expiration": expiration_timestamp,
    }

    logger.info(
        f"Adding/updating VIP expiration for {player_id=} {description=} {expiration_timestamp=}"
    )
    res = await client.post(url=url, data=payload)
    res_body: RconAPIResponse = res.json()
    return res_body


async def remove_vip(
    client: httpx.AsyncClient,
    player_id: str,
    server_url: str = CRCON_URL,
    endpoint: str = "remove_vip",
):
    url = urljoin(server_url, endpoint)
    payload = {
        "player_id": player_id,
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
    payload = {"player_id": player_id, "flag": flag, "comment": comment}

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
        vip["player_id"]: VipPlayer(
            player_id=vip["player_id"],
            name=vip["name"],
            expiration_date=vip["vip_expiration"],
        )
        for vip in raw_vips
    }


async def fetch_player(
    client: httpx.AsyncClient,
    player_id: str,
    rcon_url: str = CRCON_URL,
    endpoint: str = "api/get_player_profile",
) -> PlayerProfileType | None:
    params = {"player_id": player_id}
    url = urljoin(rcon_url, endpoint)
    res = await client.get(url=url, params=params)

    res_body: RconAPIResponse = res.json()
    return res_body["result"]


async def fetch_players(
    client: httpx.AsyncClient, player_ids: list[str]
) -> dict[str, PlayerProfileType]:
    results = {}
    async with asyncio.TaskGroup() as tg:
        for player_id in player_ids:
            task = tg.create_task(fetch_player(client=client, player_id=player_id))
            results[player_id] = task

    return {k: v.result() for k, v in results.items()}


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


async def fetch_primary_server_details(
    client: httpx.AsyncClient,
    rcon_url: str = CRCON_URL,
    endpoint: str = "api/get_connection_info",
) -> ServerDetails:
    url = urljoin(rcon_url, endpoint)
    res = await client.get(url=url)

    res_body: RconAPIResponse = res.json()

    return {
        "name": res_body["result"]["name"],
        "server_number": res_body["result"]["server_number"],
        "link": res_body["result"]["link"],
    }


async def fetch_secondary_server_details(
    client: httpx.AsyncClient,
    rcon_url: str = CRCON_URL,
    endpoint: str = "api/get_server_list",
) -> dict[str, ServerDetails]:
    url = urljoin(rcon_url, endpoint)
    res = await client.get(url=url)

    res_body: RconAPIResponse = res.json()

    return {
        str(v["server_number"]): {
            "name": v["name"],
            "server_number": v["server_number"],
            "link": v["link"],
        }
        for v in res_body["result"]
    }


async def fetch_server_details(
    client: httpx.AsyncClient,
    rcon_url: str = CRCON_URL,
) -> dict[str, ServerDetails]:
    # TODO: run in task group
    primary_server = await fetch_primary_server_details(
        client=client, rcon_url=rcon_url
    )
    secondary_servers = await fetch_secondary_server_details(
        client=client, rcon_url=rcon_url
    )

    details: dict[str, ServerDetails] = {}
    details[str(primary_server["server_number"])] = primary_server

    return details | secondary_servers
