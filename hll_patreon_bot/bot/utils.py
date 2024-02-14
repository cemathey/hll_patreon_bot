import locale
from typing import Callable, Iterable, TypeVar

import discord
from bot.constants import AUTHORIZED_DISCORD_ROLES
from bot.models import Discord, Patreon, Player
from discord.commands import ApplicationContext
from discord.role import Role
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

T = TypeVar("T")


def one_or_none(predicate: Callable[[T], bool], items: Iterable[T]) -> T | None:
    return next(filter(predicate, items), None)


async def raise_on_4xx_5xx(response):
    response.raise_for_status()


async def with_permission(ctx: ApplicationContext):
    discord_roles: list[Role] = ctx.author.roles  # type: ignore
    if any(role in AUTHORIZED_DISCORD_ROLES for role in discord_roles):
        yield ctx
    else:
        await ctx.send(
            "You don't have permission to use this command, please open a ticket"
        )
        return


def user_as_unique_name(user: discord.User):
    return f"{user.name}#{user.discriminator}"


def _get_discord_record(session: Session, discord_user_name: str) -> Discord | None:
    stmt = select(Discord).where(Discord.discord_name == discord_user_name)
    return session.scalars(stmt).one_or_none()


def _get_patreon_record(session: Session, patreon_id: str) -> Patreon | None:
    stmt = select(Patreon).where(Patreon.patreon_id == patreon_id)
    return session.scalars(stmt).one_or_none()


def _get_crcon_record(session: Session, player_id: str) -> Player | None:
    stmt = select(Player).where(Player.player_id == player_id)
    return session.scalars(stmt).one_or_none()


def get_discord_record(session: Session, discord_user_name: str) -> Discord | None:
    return _get_discord_record(session=session, discord_user_name=discord_user_name)


def get_set_discord_record(session: Session, discord_user_name: str) -> Discord:
    discord_record = _get_discord_record(
        session=session, discord_user_name=discord_user_name
    )

    if not discord_record:
        discord_record = Discord(discord_name=discord_user_name)
        logger.warning(f"Creating new discord record {discord_record}")
        session.add(discord_record)

    return discord_record


def get_patreon_record(session: Session, patreon_id: str) -> Patreon | None:
    return _get_patreon_record(session=session, patreon_id=patreon_id)


def get_set_patreon_record(
    session: Session, discord_record: Discord, patreon_id: str
) -> Patreon:
    patreon_record = _get_patreon_record(session=session, patreon_id=patreon_id)

    if not patreon_record:
        patreon_record = Patreon(patreon_id=patreon_id, discord=discord_record)
        logger.warning(
            f"Creating new patreon record {patreon_record} for {discord_record}"
        )
        session.add(patreon_record)

    return patreon_record


def get_crcon_record(session: Session, player_id: str) -> Player | None:
    return _get_crcon_record(session=session, player_id=player_id)


def get_set_crcon_record(
    session: Session, discord_record: Discord, player_id: str, main: bool
) -> Player:
    player_record = _get_crcon_record(session=session, player_id=player_id)

    if not player_record:
        player_record = Player(player_id=player_id, main=main, discord=discord_record)
        logger.warning(
            f"Creating new player record {player_record} for {discord_record}"
        )
        session.add(player_record)

    return player_record


def cents_as_currency(cents: int) -> str:
    locale.setlocale(locale.LC_ALL, "")
    return locale.currency(cents / 100, symbol=True, grouping=True)


def link_patreon_to_discord(session: Session, patreon_id: str, discord_name: str):
    patreon_id_already_linked = False
    previous_linked_discord: str | None = None

    discord_record = get_set_discord_record(
        session=session, discord_user_name=discord_name
    )

    patreon_record = get_patreon_record(session=session, patreon_id=patreon_id)
    if patreon_record is None:
        patreon_record = get_set_patreon_record(
            session=session, discord_record=discord_record, patreon_id=patreon_id
        )
        logger.warning(f"{patreon_record} linked to {discord_record}")
    elif patreon_record and not patreon_record.discord:
        patreon_record.discord = discord_record
        logger.warning(f"{patreon_record} linked to {discord_record}")
    elif patreon_record and patreon_record.discord:
        patreon_id_already_linked = True
        previous_linked_discord = patreon_record.discord.discord_name
        patreon_record.discord = discord_record
        logger.warning(
            f"{discord_record!r} previously linked to {patreon_record.discord.discord_name} now linked to {discord_record.discord_name}"
        )

    return patreon_id_already_linked, previous_linked_discord


def unlink_patreon_from_discord(
    session: Session, patreon_id: str, discord_name: str
) -> str | None:
    discord_record = get_set_discord_record(
        session=session, discord_user_name=discord_name
    )

    if discord_record.patreon is None:
        return None
    elif discord_record.patreon == patreon_id:
        session.delete(discord_record.patreon)
    else:
        return discord_record.patreon.patreon_id


def link_primary_crcon_to_discord(
    session: Session, player_id: str, discord_name: str
) -> tuple[bool, str | None]:
    player_id_already_linked = False
    previous_linked_discord: str | None = None

    discord_record = get_set_discord_record(
        session=session, discord_user_name=discord_name
    )
    player_record = get_set_crcon_record(
        session=session,
        discord_record=discord_record,
        player_id=player_id,
        main=True,
    )

    if player_record.discord:
        player_id_already_linked = True
        previous_linked_discord = player_record.discord.discord_name

    player_record.discord = discord_record

    return player_id_already_linked, previous_linked_discord


def unlink_primary_crcon_from_discord(session: Session, discord_name: str) -> list[str]:
    deleted_player_ids: list[str] = []
    discord_record = get_set_discord_record(
        session=session, discord_user_name=discord_name
    )
    for player in discord_record.players:
        deleted_player_ids.append(player.player_id)
        session.delete(player)

    return deleted_player_ids


def link_sponsored_crcon_to_discord(
    session: Session, discord_name: str, player_id: str
) -> tuple[bool, str | None]:
    player_id_already_linked = False
    previous_linked_discord = None

    discord_record = get_set_discord_record(
        session=session, discord_user_name=discord_name
    )
    player_record = get_set_crcon_record(
        session=session,
        discord_record=discord_record,
        player_id=player_id,
        main=False,
    )

    # A CRCON account
    if player_record.discord:
        player_id_already_linked = True
        previous_linked_discord = player_record.discord.discord_name

    player_record.discord = discord_record

    return player_id_already_linked, previous_linked_discord


def unlink_sponsored_crcon_from_discord(session: Session, player_id: str):
    pass
