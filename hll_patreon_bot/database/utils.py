from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from hll_patreon_bot.database.models import Discord, DiscordPlayers, Patreon, Player


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
    session: Session, discord_record: Discord, player_id: str
) -> Player:
    player_record = _get_crcon_record(session=session, player_id=player_id)

    if not player_record:
        player_record = Player(player_id=player_id)
        logger.warning(
            f"Creating new player record {player_record} for {discord_record}"
        )
        session.add(player_record)

    return player_record


def get_primary_crcon_record(session: Session, discord_user_name: str) -> Player | None:
    discord_record = get_set_discord_record(
        session=session, discord_user_name=discord_user_name
    )
    stmt = (
        select(DiscordPlayers)
        .where(DiscordPlayers.discord == discord_record)
        .where(DiscordPlayers.main == True)
    )
    discord_player = session.scalars(stmt).one_or_none()

    if discord_player:
        return discord_player.player


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
        logger.warning(
            f"Tried to unlink {patreon_id} from {discord_record} but it was not already linked"
        )
        return None
    if discord_record.patreon.patreon_id == patreon_id:
        logger.warning(f"Unlinked {discord_record.patreon} from {discord_record}")
        session.delete(discord_record.patreon)
    else:
        logger.warning(
            f"Tried to unlink {patreon_id} from {discord_record} but it is linked to {discord_record.patreon}"
        )

    return discord_record.patreon.patreon_id


def link_primary_crcon_to_discord(
    session: Session, player_id: str, discord_name: str
) -> str | None:
    previous_linked_discord: str | None = None

    discord_record = get_set_discord_record(
        session=session, discord_user_name=discord_name
    )

    player_record = get_set_crcon_record(
        session=session,
        discord_record=discord_record,
        player_id=player_id,
    )

    stmt = (
        select(DiscordPlayers).where(DiscordPlayers.discord == discord_record)
        # .where(DiscordPlayers.player_id == player_record.id)
        .where(DiscordPlayers.main == True)
    )
    discord_player = session.scalars(stmt).one_or_none()

    if discord_player:
        previous_linked_discord = discord_player.discord.discord_name
        logger.warning(
            f"Linked {player_record} to {discord_record} was previously linked to {discord_player.discord}"
        )
        discord_player.discord = discord_record
    else:
        discord_player = DiscordPlayers()
        discord_player.discord = discord_record
        discord_player.player = player_record
        discord_player.main = True
        session.add(discord_player)
        logger.warning(f"Linked {player_record} to {discord_record}")

    return previous_linked_discord


def unlink_primary_crcon_from_discord(
    session: Session, discord_name: str
) -> str | None:
    deleted_player: str | None = None
    discord_record = get_set_discord_record(
        session=session, discord_user_name=discord_name
    )

    stmt = (
        select(DiscordPlayers)
        .where(DiscordPlayers.discord == discord_record)
        .where(DiscordPlayers.main == True)
    )
    discord_player = session.scalars(stmt).one_or_none()
    if discord_player:
        deleted_player = discord_player.player.player_id
        session.delete(discord_player)
        logger.warning(
            f"Unlinked primary {discord_player.player} from {discord_player.discord}"
        )
    else:
        logger.warning(
            f"Tried to unlink primary for {discord_record} but they weren't linked"
        )

    return deleted_player


def link_sponsored_crcon_to_discord(
    session: Session, discord_name: str, player_id: str
) -> str | None:
    previous_linked_discord: str | None = None

    discord_record = get_set_discord_record(
        session=session, discord_user_name=discord_name
    )

    player_record = get_set_crcon_record(
        session=session,
        discord_record=discord_record,
        player_id=player_id,
    )

    stmt = (
        select(DiscordPlayers)
        .where(DiscordPlayers.discord == discord_record)
        .where(DiscordPlayers.player == player_record)
        .where(DiscordPlayers.main == False)
    )

    discord_player = session.scalars(stmt).one_or_none()
    if discord_player:
        previous_linked_discord = discord_player.discord.discord_name
        logger.warning(
            f"Tried to link {player_record} to {discord_record} but it was already linked"
        )
    else:
        discord_player = DiscordPlayers()
        discord_player.discord = discord_record
        discord_player.player = player_record
        session.add(discord_player)

    return previous_linked_discord


def unlink_sponsored_crcon_from_discord(
    session: Session, discord_name: str, player_id: str
):
    discord_record = get_set_discord_record(
        session=session, discord_user_name=discord_name
    )

    player_record = get_crcon_record(session=session, player_id=player_id)

    if player_record is None:
        return

    stmt = (
        select(DiscordPlayers)
        .where(DiscordPlayers.discord == discord_record)
        .where(DiscordPlayers.player == player_record)
        .where(DiscordPlayers.main == False)
    )

    discord_player = session.scalars(stmt).one_or_none()
    if discord_player:
        logger.warning(f"Unlinking {player_record} from {discord_record}")
        session.delete(discord_player)
    else:
        logger.warning(
            f"Tried to unlink {player_record} from {discord_record} but it was not linked"
        )
