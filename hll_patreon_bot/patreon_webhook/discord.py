from datetime import datetime, timezone
from typing import Callable, Type

import discord
from bot.utils import cents_as_currency
from patreon_webhook.constants import (
    ACTION_CREATE,
    ACTION_DELETE,
    ACTION_UPDATE,
    PATREON_HEADERS,
    PATREON_TRIGGER_DELIMITER,
    RESOURCE_MEMBER,
    RESOURCE_PLEDGE,
)
from patreon_webhook.types import (
    PatreonMemberWH,
    PatreonPledgeWH,
    PatreonTriggerAction,
    PatreonTriggerResource,
    PatreonWebhook,
)


def _create_patreon_webhook_embed(
    title: str, data: PatreonMemberWH | PatreonPledgeWH
) -> discord.Embed:
    embed = discord.Embed()
    embed.timestamp = datetime.now(tz=timezone.utc)
    embed.title = title

    last_charge_date_raw = data.get("last_charge_date")

    if isinstance(last_charge_date_raw, datetime):
        last_charge_date = f"<t:{int(last_charge_date_raw.timestamp())}:f>"
    else:
        last_charge_date = "None"

    currently_entitled_amount_cents_raw = data.get("currently_entitled_amount_cents")

    if isinstance(currently_entitled_amount_cents_raw, int):
        currently_entitled_amount_cents = cents_as_currency(
            currently_entitled_amount_cents_raw
        )
    else:
        currently_entitled_amount_cents = "None"

    embed.add_field(name="Patreon ID", value=data.get("id"))
    embed.add_field(name="Email:", value=data["email"] if data["email"] else "")
    embed.add_field(
        name="Currently Entitled Amount", value=currently_entitled_amount_cents
    )
    embed.add_field(name="Last Charge Date", value=last_charge_date)
    embed.add_field(
        name="Last Charge Status", value=str(data["last_charge_status"].value)
    )
    embed.add_field(name="Patron Status", value=str(data["patron_status"].value))

    return embed


def create_member_creation_embed(
    data: PatreonMemberWH, title: str = "New Member Signup"
) -> discord.Embed:
    embed = _create_patreon_webhook_embed(title=title, data=data)

    return embed


def create_member_deletion_embed(
    data: PatreonMemberWH, title: str = "Member Unsubscribed"
) -> discord.Embed:
    embed = _create_patreon_webhook_embed(title=title, data=data)

    return embed


def create_member_update_embed(
    data: PatreonMemberWH, title: str = "Member Updated"
) -> discord.Embed:
    embed = _create_patreon_webhook_embed(title=title, data=data)

    return embed


def create_pledge_creation_embed(
    data: PatreonPledgeWH, title: str = "Pledge Created"
) -> discord.Embed:
    embed = _create_patreon_webhook_embed(title=title, data=data)

    return embed


def create_pledge_deletion_embed(
    data: PatreonPledgeWH, title: str = "Pledge Cancelled"
) -> discord.Embed:
    embed = _create_patreon_webhook_embed(title=title, data=data)

    return embed


def create_pledge_update_embed(
    data: PatreonPledgeWH, title: str = "Pledge Updated"
) -> discord.Embed:
    embed = _create_patreon_webhook_embed(title=title, data=data)

    return embed


def lookup_action_embed(
    event: PatreonWebhook, data: PatreonMemberWH | PatreonPledgeWH
) -> discord.Embed:
    if event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        action=PatreonTriggerAction.CREATE,
    ):
        return create_member_creation_embed(data=data)  # type: ignore
    elif event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        action=PatreonTriggerAction.DELETE,
    ):
        return create_member_deletion_embed(data=data)  # type: ignore
    elif event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        action=PatreonTriggerAction.UPDATE,
    ):
        return create_member_update_embed(data=data)  # type: ignore
    elif event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        sub_resource=PatreonTriggerResource.PLEDGE,
        action=PatreonTriggerAction.CREATE,
    ):
        return create_pledge_creation_embed(data=data)  # type: ignore
    elif event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        sub_resource=PatreonTriggerResource.PLEDGE,
        action=PatreonTriggerAction.DELETE,
    ):
        return create_pledge_deletion_embed(data=data)  # type: ignore
    elif event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        sub_resource=PatreonTriggerResource.PLEDGE,
        action=PatreonTriggerAction.UPDATE,
    ):
        return create_pledge_update_embed(data=data)  # type: ignore
    else:
        raise ValueError(f"Unmatched {event}")
