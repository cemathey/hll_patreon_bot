from datetime import datetime, timedelta, timezone

import httpx
from loguru import logger
from patreon_webhook.types import (
    PatreonMemberWH,
    PatreonPledgeWH,
    PatreonTriggerAction,
    PatreonTriggerResource,
    PatreonWebhook,
)
from patreon_webhook.utils import (
    calc_vip_expiration_timestamp,
    parse_patreon_member_webhook,
    parse_patreon_pledge_webhook,
)

from hll_patreon_bot.bot.constants import MISSING_PLAYER_NAME
from hll_patreon_bot.database.models import enter_session
from hll_patreon_bot.database.utils import get_patreon_record, link_patreon_to_discord
from hll_patreon_bot.integrations.crcon.crcon import (
    add_vip,
    fetch_current_expiration,
    fetch_current_vips,
)


async def handle_member_create(client: httpx.AsyncClient, data: PatreonPledgeWH):
    """Link a Patreon ID to a Discord user if linked on Patreons website"""
    # If they've linked their Discord in Patreon, create/link Discord record
    # Patreon's bot will handle role change
    if (discord_name := data["discord_user_id"]) is None:
        return

    with enter_session() as session:
        link_patreon_to_discord(
            session=session, patreon_id=data["id"], discord_name=discord_name
        )


async def handle_member_delete(client: httpx.AsyncClient, data: PatreonPledgeWH):
    """Not currently used to retain historical info"""
    # what do we need to do if a person deletes their patreon
    # VIP will expire naturally
    # do we really want to delete their patreon record or unlink their discord?
    # destroys historical info for minimal db size reduction
    pass

    # with enter_session() as session:
    #     patreon = get_patreon_record(session=session, patreon_id=data["id"])
    #     if patreon and patreon.discord:
    #         pass


async def handle_member_update(client: httpx.AsyncClient, data: PatreonPledgeWH):
    """Link a Patreon ID to a Discord user if linked or changed on Patreons website"""
    patreon_id = data["id"]
    discord_name = data["discord_user_id"]

    if not discord_name:
        logger.info(f"{patreon_id} updated, no discord linked")
        return

    with enter_session() as session:
        link_patreon_to_discord(
            session=session, patreon_id=patreon_id, discord_name=discord_name
        )


async def handle_pledge_create(client: httpx.AsyncClient, data: PatreonPledgeWH):
    # same as handle_pledge_update, so just call that for now
    return await handle_pledge_update(client=client, data=data)


async def handle_pledge_delete(client: httpx.AsyncClient, data: PatreonPledgeWH):
    # No action should be required, if they have VIP it will be automatically removed
    pass


async def handle_pledge_update(client: httpx.AsyncClient, data: PatreonPledgeWH):
    # If they are a current patron and payment status is paid
    # add the difference between their next charge date and now to their current VIP expiration
    # or if no expiration, set it the next charge date
    # logger.info(f"{data=}")

    patreon_id = data["id"]
    patreon_status = data["patron_status"]
    last_charge_status = data["last_charge_status"]
    last_charge_date = data["last_charge_date"]
    next_charge_date = data["next_charge_date"]

    # TODO: make this configurable
    if not next_charge_date:
        next_charge_date = last_charge_date + timedelta(days=30)

    with enter_session() as session:
        # if we don't have any linked CRCONs, bail out
        patreon_record = get_patreon_record(session=session, patreon_id=patreon_id)

        if patreon_record is None:
            logger.warning(
                f"Could not update VIP expiration for {patreon_id} no patreon record exists"
            )
            return

        # TODO: do we need to check patreon status and not just last charge?
        if patreon_status.is_successful() and last_charge_status.is_successful():
            earned_time = next_charge_date - datetime.now(tz=timezone.utc)

            # only the day component of a timedelta will ever be negative
            if earned_time.days < 0:
                logger.error(f"{earned_time=} for {patreon_record} was < 0")
            else:
                current_vips = await fetch_current_vips(client=client)

                # Update every associated CRCON player
                modified_players = False
                for discord_player in patreon_record.discord.players:
                    modified_players = True
                    player_id = discord_player.player.player_id
                    vip_info = current_vips.get(player_id)
                    vip_name = vip_info.name if vip_info else MISSING_PLAYER_NAME
                    current_expiration = await fetch_current_expiration(
                        client=client, player_id=player_id
                    )

                    new_expiration = calc_vip_expiration_timestamp(
                        earned=earned_time,
                        current_expiration=(
                            current_expiration["expiration"]
                            if current_expiration
                            else None
                        ),
                    )

                    logger.info(
                        f"Adding/updating VIP expiration for {player_id=} {vip_name=} {current_expiration=} {new_expiration=}"
                    )
                    await add_vip(
                        client=client,
                        player_id=player_id,
                        name=vip_name,
                        expiration_timestamp=new_expiration,
                    )

                if not modified_players:
                    logger.warning(
                        f"{patreon_record} has no linked player accounts to update VIP expirations for"
                    )


def lookup_parser(event: PatreonWebhook):
    if event.sub_resource is None:
        return parse_patreon_member_webhook
    elif (
        event.resource == PatreonTriggerResource.MEMBER
        and event.sub_resource == PatreonTriggerResource.PLEDGE
    ):
        return parse_patreon_pledge_webhook
    else:
        raise ValueError(f"No parser found for {event=}")


async def lookup_action(
    event: PatreonWebhook,
    client: httpx.AsyncClient,
    data: PatreonMemberWH | PatreonPledgeWH,
):
    if event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        action=PatreonTriggerAction.CREATE,
    ):
        return await handle_member_create(client=client, data=data)  # type: ignore
    elif event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        action=PatreonTriggerAction.DELETE,
    ):
        return await handle_member_delete(client=client, data=data)  # type: ignore
    elif event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        action=PatreonTriggerAction.UPDATE,
    ):
        return await handle_member_update(client=client, data=data)  # type: ignore
    elif event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        sub_resource=PatreonTriggerResource.PLEDGE,
        action=PatreonTriggerAction.CREATE,
    ):
        return await handle_pledge_create(client=client, data=data)  # type: ignore
    elif event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        sub_resource=PatreonTriggerResource.PLEDGE,
        action=PatreonTriggerAction.DELETE,
    ):
        return await handle_pledge_delete(client=client, data=data)  # type: ignore
    elif event == PatreonWebhook(
        resource=PatreonTriggerResource.MEMBER,
        sub_resource=PatreonTriggerResource.PLEDGE,
        action=PatreonTriggerAction.UPDATE,
    ):
        return await handle_pledge_update(client=client, data=data)  # type: ignore
    else:
        raise ValueError(f"Unmatched {event}")
