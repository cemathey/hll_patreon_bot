import sqlite3
from datetime import datetime, timezone

import pytest
from freezegun import freeze_time
from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError, PendingRollbackError
from sqlalchemy.orm import Session

from hll_patreon_bot.database.models import (
    Base,
    Discord,
    DiscordPlayers,
    Patreon,
    Player,
)


@pytest.fixture
def session():
    # in memory database
    engine = create_engine("sqlite://", echo=False)

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.begin()
        try:
            yield session
        except:
            session.rollback()
            raise
        else:
            session.commit()
        finally:
            session.close()


@pytest.fixture
def session_no_commit():
    # in memory database
    engine = create_engine("sqlite://")

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.begin()
        try:
            yield session
        except:
            session.rollback()
            raise
        finally:
            session.close()


def test_model_creation(session: Session):
    stmt = select(Discord).filter(Discord.id == 1)
    res = session.scalars(stmt).one_or_none()
    assert res is None


def test_discord_disallows_duplicate_names(session_no_commit: Session):
    a = Discord(discord_name="name")
    b = Discord(discord_name="name")

    with pytest.raises(IntegrityError):
        session_no_commit.add(a)
        session_no_commit.add(b)
        session_no_commit.commit()


@pytest.mark.parametrize(
    "model, payload",
    [
        (Discord, {"discord_name": "some dude"}),
        (Patreon, {"patreon_id": "4321", "discord_id": 1}),
    ],
)
def test_created_at_times(session: Session, model, payload):
    record = model(**payload)
    session.add(record)
    session.commit()

    assert record.created_at <= datetime.now(tz=timezone.utc).replace(tzinfo=None)


def test_relationships(session: Session):
    d1 = Discord(discord_name="discord#0")
    d2 = Discord(discord_name="discord#1")

    pat1 = Patreon(patreon_id="abcd")
    pat1.discord = d1

    p1 = Player(player_id="1234")
    p2 = Player(player_id="4321")
    p3 = Player(player_id="5678")
    p4 = Player(player_id="8765")

    # Allow multiple sponsored
    d1_p1 = DiscordPlayers(main=True, discord=d1, player=p1)
    d1_p2 = DiscordPlayers(main=False, discord=d1, player=p2)
    d1_p3 = DiscordPlayers(main=False, discord=d1, player=p3)

    session.add_all([d1, d2, pat1, p1, p2, p3, p4, d1_p1, d1_p2, d1_p3])
    session.commit()

    logger.error(f"{d1=}")
    logger.error(f"{pat1=}")
    logger.error(f"{p1=}")
    logger.error(f"{d1_p1=}")
    # logger.error(f"{d1.players=}")
    logger.error(f"{[f'id={p.player.player_id} main={p.main}' for p in d1.players]}")
    # assert False


def test_patreon_discord_mandatory(session_no_commit: Session):
    pat1 = Patreon(patreon_id="abcd")
    with pytest.raises(IntegrityError):
        session_no_commit.add(pat1)
        session_no_commit.commit()


def test_player_discord_optional(session: Session):
    p1 = Player(player_id="1234")
    session.add(p1)


def test_discord_player_patreon_optional(session: Session):
    d1 = Discord(discord_name="discord#0")
    session.add(d1)


def test_can_link_multiple_sponsored_player_ids(session: Session):
    p1 = Player(player_id="1234")
    p2 = Player(player_id="4321")

    d1 = Discord(discord_name="asdf#0")

    d1_p1 = DiscordPlayers(discord=d1, player=p1)
    d1_p2 = DiscordPlayers(discord=d1, player=p2)

    session.add(d1_p1)
    session.add(d1_p2)


def test_player_can_be_sponsored_by_multiple_discords(session: Session):
    p1 = Player(player_id="1234")

    d1 = Discord(discord_name="asdf#0")
    d2 = Discord(discord_name="ghjk#0")

    d1_p1 = DiscordPlayers(discord=d1, player=p1)
    d2_p1 = DiscordPlayers(discord=d2, player=p1)

    session.add(d1_p1)
    session.add(d2_p1)
