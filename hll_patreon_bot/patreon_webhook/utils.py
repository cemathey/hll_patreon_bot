from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

from patreon_webhook.types import (
    ChargeStatus,
    PatreonMemberWH,
    PatreonPledgeWH,
    PatronStatus,
)


def calc_vip_expiration_timestamp(
    earned: timedelta,
    current_expiration: datetime | None,
    from_time: datetime | None = None,
) -> datetime:
    """Return the players new expiration date accounting for reward/existing timestamps"""
    from_time = from_time or datetime.now(tz=timezone.utc)

    if current_expiration is None:
        timestamp = from_time + earned
        return timestamp

    return current_expiration + earned


def parse_patreon_pledge_webhook(data: dict[str, Any]) -> PatreonPledgeWH:
    parsed: dict[str, Any] = {}

    parsed: dict[str, Any] = {}

    parsed["id"] = data["data"]["id"]
    parsed["currently_entitled_amount_cents"] = data["data"]["attributes"].get(
        "currently_entitled_amount_cents"
    )

    parsed["email"] = data["data"]["attributes"].get("email")
    parsed["last_charge_date"] = data["data"]["attributes"]["last_charge_date"]
    parsed["last_charge_status"] = data["data"]["attributes"]["last_charge_status"]
    parsed["patron_status"] = data["data"]["attributes"]["patron_status"]
    parsed["next_charge_date"] = data["data"]["attributes"].get("next_charge_date")

    try:
        for obj in data["included"]:
            if obj["type"] == "user":
                raw_discord = (
                    obj["attributes"].get("social_connections", {}).get("discord", {})
                )
                parsed["discord_user_id"] = (
                    raw_discord.get("user_id") if raw_discord else None
                )
    except KeyError:
        parsed["discord_user_id"] = None

    typed_data: PatreonPledgeWH = {
        "id": parsed["id"],
        "currently_entitled_amount_cents": (
            int(parsed["currently_entitled_amount_cents"])
            if parsed["currently_entitled_amount_cents"]
            else None
        ),
        "email": parsed["email"],
        "last_charge_date": datetime.fromisoformat(parsed["last_charge_date"]),
        "last_charge_status": ChargeStatus[parsed["last_charge_status"].lower()],
        "next_charge_date": (
            datetime.fromisoformat(parsed["next_charge_date"])
            if parsed["next_charge_date"]
            else None
        ),
        "patron_status": PatronStatus(parsed["patron_status"]),
        "discord_user_id": parsed["discord_user_id"],
    }

    return typed_data


def parse_patreon_member_webhook(data: dict[str, Any]) -> PatreonMemberWH:
    parsed: dict[str, Any] = {}

    parsed["id"] = data["data"]["id"]
    parsed["currently_entitled_amount_cents"] = data["data"]["attributes"].get(
        "currently_entitled_amount_cents"
    )

    parsed["email"] = data["data"]["attributes"]["email"]
    parsed["last_charge_date"] = data["data"]["attributes"]["last_charge_date"]
    parsed["last_charge_status"] = data["data"]["attributes"]["last_charge_status"]
    parsed["patron_status"] = data["data"]["attributes"]["patron_status"]

    try:
        for obj in data["included"]:
            if obj["type"] == "user":
                raw_discord = (
                    obj["attributes"].get("social_connections", {}).get("discord", {})
                )
                parsed["discord_user_id"] = (
                    raw_discord.get("user_id") if raw_discord else None
                )
    except KeyError:
        parsed["discord_user_id"] = None

    typed_data: PatreonMemberWH = {
        "id": parsed["id"],
        "currently_entitled_amount_cents": int(
            parsed["currently_entitled_amount_cents"]
        ),
        "email": parsed["email"],
        "last_charge_date": datetime.fromisoformat(parsed["last_charge_date"]),
        "last_charge_status": ChargeStatus[parsed["last_charge_status"].lower()],
        "patron_status": PatronStatus(parsed["patron_status"]),
        "discord_user_id": parsed["discord_user_id"],
    }

    return typed_data
