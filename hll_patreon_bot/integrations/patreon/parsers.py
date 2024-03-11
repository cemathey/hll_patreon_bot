import json
from collections import defaultdict
from datetime import datetime
from typing import Any

from loguru import logger

from hll_patreon_bot.integrations.patreon.types import (
    ChargeStatus,
    PatreonCampaignMember,
    PatreonMember,
    PatreonUserAttributes,
    PatronStatus,
    PledgeEventType,
    PledgeHistory,
)


def parse_pledge(data: dict[str, Any]) -> PledgeHistory:
    attributes = data["attributes"]

    id_: str = data["id"]

    if id_ in (
        "pledge_start:158942977",
        "pledge_delete:92396917",
        "subscription:1074504017"
        "subscription:1055880151"
        "subscription:1037223396"
        "subscription:1018598369"
        "subscription:999818207",
        "subscription:981011500",
        "subscription:962259248",
        "subscription:935309044",
        "subscription:908283319",
        "subscription:881317045",
        "pledge_start:92396917",
    ):
        logger.error(f"parse_pledge data={json.dumps(data)}")

    type_: PledgeEventType = PledgeEventType(attributes["type"])
    amount_cents: int = int(attributes.get("amount_cents", 0))
    date: datetime = datetime.fromisoformat(attributes.get("date"))
    status: ChargeStatus = ChargeStatus[
        (
            attributes["payment_status"].lower()
            if attributes["payment_status"]
            else "none"
        )
    ]
    tier_id: str = attributes["tier_id"]

    return {
        "id": id_,
        "type": type_,
        "amount_cents": amount_cents,
        "date": date,
        "status": status,
        "tier_id": tier_id,
    }


def parse_member(data: dict[str, Any]) -> PatreonMember:
    """Parse data from Patreons member endpoint

    This is very similar to the Patreon webhook parser but defined separately
    in case we need to handle any special cases
    """
    id_: str = data["data"]["id"]
    if id_ == "52c7b310-8d73-4ce8-bfba-ef1caa58eb4e":
        logger.info(f"data={data}")

    currently_entitled_amount_cents: int = data["data"]["attributes"].get(
        "currently_entitled_amount_cents", 0
    )
    name: str = data["data"]["attributes"]["full_name"]
    email: str = data["data"]["attributes"]["email"]
    last_charge_date: str | None = data["data"]["attributes"]["last_charge_date"]
    last_charge_status: str | None = data["data"]["attributes"]["last_charge_status"]
    next_charge_date: str | None = data["data"]["attributes"].get("next_charge_date")
    patron_status: str = data["data"]["attributes"]["patron_status"]

    discord_user_id: int | None = None
    thumb_url: str | None = None

    pledge_history: list[PledgeHistory] = []
    try:
        for obj in data["included"]:
            if obj["type"] == "user":
                raw_discord = (
                    obj["attributes"].get("social_connections", {}).get("discord", {})
                )
                discord_user_id = (
                    int(raw_discord.get("user_id")) if raw_discord else None
                )
                thumb_url = obj["attributes"].get("thumb_url")
            elif obj["type"] == "pledge-event":
                if id_ == "52c7b310-8d73-4ce8-bfba-ef1caa58eb4e":
                    logger.info(f"{obj}")
                pledge_history.append(parse_pledge(obj["attributes"]))

    except KeyError:
        # The user might not have a social connection dict for Discord
        discord_user_id = None

    note: str = data["data"]["attributes"]["note"]

    typed_data: PatreonMember = {
        "id": id_,
        "email": email,
        "name": name,
        "currently_entitled_amount_cents": currently_entitled_amount_cents,
        "last_charge_date": (
            datetime.fromisoformat(last_charge_date) if last_charge_date else None
        ),
        "next_charge_date": (
            datetime.fromisoformat(next_charge_date) if next_charge_date else None
        ),
        "last_charge_status": ChargeStatus[
            (last_charge_status.lower() if last_charge_status else "none")
        ],
        "patron_status": (
            PatronStatus[patron_status] if patron_status else PatronStatus.none
        ),
        "discord_user_id": int(discord_user_id) if discord_user_id else None,
        "note": note,
        "thumb_url": thumb_url,
        "pledge_history": pledge_history,
    }

    return typed_data


def _parse_campaign_member(data: dict[str, Any]) -> PatreonCampaignMember:
    """Parse data from Patreons campaign members endpoint

    This is very similar to parse_member but the data/includes are structured differently
    """
    id_: str = data["id"]
    user_id: str = data["relationships"]["user"]["data"]["id"]
    currently_entitled_amount_cents: int = data["attributes"].get(
        "currently_entitled_amount_cents", 0
    )
    name: str = data["attributes"]["full_name"]
    email: str = data["attributes"]["email"]
    last_charge_date: str | None = data["attributes"]["last_charge_date"]
    last_charge_status: str | None = data["attributes"]["last_charge_status"]
    next_charge_date: str | None = data["attributes"].get("next_charge_date")
    patron_status: str = data["attributes"]["patron_status"]
    note: str = data["attributes"]["note"]
    pledge_ids: set[str] = set()

    # logger.warning(f"data= {json.dumps(data)}")

    for obj in data["relationships"].get("pledge_history", {}).get("data"):
        if id_ == "52c7b310-8d73-4ce8-bfba-ef1caa58eb4e":
            logger.info(f"obj={obj}")
        pledge_ids.add(obj["id"])

    typed_data: PatreonCampaignMember = {
        "id": id_,
        "user_id": user_id,
        "email": email,
        "name": name,
        "currently_entitled_amount_cents": currently_entitled_amount_cents,
        "last_charge_date": (
            datetime.fromisoformat(last_charge_date) if last_charge_date else None
        ),
        "next_charge_date": (
            datetime.fromisoformat(next_charge_date) if next_charge_date else None
        ),
        "last_charge_status": ChargeStatus[
            (last_charge_status.lower() if last_charge_status else "none")
        ],
        "patron_status": (
            PatronStatus[patron_status] if patron_status else PatronStatus.none
        ),
        "note": note,
        "pledge_ids": pledge_ids,
    }

    return typed_data


def parse_campaign_members(data: dict[str, Any]) -> dict[str, PatreonMember]:
    raw_members: dict[str, PatreonCampaignMember] = {}

    # by member ID
    member_lookup: dict[str, PatreonMember] = {}

    # by pledge ID
    pledge_history_lookup: dict[str, PledgeHistory] = {}

    # by user ID
    user_lookup: dict[str, PatreonUserAttributes] = {}

    for obj in data["data"]:
        member = _parse_campaign_member(data=obj)
        raw_members[member["user_id"]] = member

    for obj in data["included"]:
        if obj["type"] == "user":
            raw_discord = (
                obj["attributes"].get("social_connections", {}).get("discord", {})
            )
            discord_user_id: str | None = (
                raw_discord.get("user_id") if raw_discord else None
            )
            thumb_url = obj["attributes"]["thumb_url"]
            user_lookup[obj["id"]] = {
                "discord_user_id": int(discord_user_id) if discord_user_id else None,
                "thumb_url": thumb_url,
            }
        elif obj["type"] == "pledge-event":
            pledge_event = parse_pledge(data=obj)
            pledge_history_lookup[obj["id"]] = pledge_event

    for member in raw_members.values():
        if member["id"] == "52c7b310-8d73-4ce8-bfba-ef1caa58eb4e":
            for p_id in member["pledge_ids"]:
                logger.info(f"{pledge_history_lookup[p_id]}")
        pledge_history = sorted(
            [
                pledge_history_lookup[p_id]
                for p_id in member["pledge_ids"]
                if pledge_history_lookup[p_id]["status"].value
            ],
            key=lambda x: x["date"],
            reverse=True,
        )
        typed_member: PatreonMember = {
            "id": member["id"],
            "name": member["name"],
            "email": member["email"],
            "currently_entitled_amount_cents": member[
                "currently_entitled_amount_cents"
            ],
            "last_charge_date": member["last_charge_date"],
            "last_charge_status": member["last_charge_status"],
            "next_charge_date": member["next_charge_date"],
            "patron_status": member["patron_status"],
            "note": member["note"],
            "discord_user_id": user_lookup[member["user_id"]]["discord_user_id"],
            "thumb_url": user_lookup[member["user_id"]]["thumb_url"],
            "pledge_history": pledge_history,
        }
        member_lookup[member["id"]] = typed_member

    return member_lookup
