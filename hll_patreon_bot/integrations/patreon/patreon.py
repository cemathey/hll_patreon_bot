import json
from typing import Any

import httpx
from loguru import logger

from hll_patreon_bot.bot.constants import PATREON_ACCESS_TOKEN, PATREON_CAMPAIGN_ID
from hll_patreon_bot.integrations.patreon.constants import (
    CAMPAIGN_MEMBERS_PARAMS,
    CAMPAIGN_MEMBERS_URL,
    MEMBER_BY_ID_PARAMS,
    MEMBER_BY_ID_URL,
)
from hll_patreon_bot.integrations.patreon.parsers import (
    parse_campaign_members,
    parse_member,
)
from hll_patreon_bot.integrations.patreon.types import PatreonMember


def get_auth_header():
    return {"Authorization": f"Bearer {PATREON_ACCESS_TOKEN}"}


async def get_member(
    client: httpx.AsyncClient,
    member_id: str,
    url: str = MEMBER_BY_ID_URL,
    includes: dict[str, str] = MEMBER_BY_ID_PARAMS,
):
    res = await client.get(
        url=url.format(member_id=member_id), params=includes, headers=get_auth_header()
    )
    # logger.error(f"{url=}")
    # logger.error(f"{json.dumps(includes)}")
    content = res.json()
    # logger.warning(f"{json.dumps(content)}")

    if res.status_code == 404:
        return None

    return parse_member(data=content)


async def get_campaign_members(
    client: httpx.AsyncClient,
    member_id: str | None = None,
    campaign_id: str = PATREON_CAMPAIGN_ID,
    url: str = CAMPAIGN_MEMBERS_URL,
    includes: dict[str, str] = CAMPAIGN_MEMBERS_PARAMS,
):
    url = url.format(campaign_id=campaign_id)
    res = await client.get(url=url, params=includes, headers=get_auth_header())
    content: dict[str, Any] = res.json()
    members: dict[str, PatreonMember] = {}

    # logger.error(f"{url=}")
    # logger.warning(f"{includes=}")
    # logger.error(f"{res.url=}")

    # logger.warning(f"{json.dumps(content)}")
    members |= parse_campaign_members(data=content)
    yield members

    while (
        next_link := content.get("links", {}).get("next")
    ) and member_id not in members:
        logger.info(
            f"Fetching next page of campaign members next_link={next_link[-10:]}"
        )
        res = await client.get(
            url=next_link, params=includes, headers=get_auth_header()
        )
        content: dict[str, Any] = res.json()
        members |= parse_campaign_members(data=content)
        yield members
