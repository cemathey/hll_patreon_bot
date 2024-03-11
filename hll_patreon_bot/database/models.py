from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator, Optional

import sqlalchemy.orm.exc
from loguru import logger
from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Table, create_engine
from sqlalchemy.event import listens_for
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

engine = create_engine("sqlite:///file:db_data/db.sqlite?mode=rwc&uri=true", echo=True)


@contextmanager
def enter_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        session.begin()
        try:
            yield session
        except:
            session.rollback()
            raise
        else:
            session.commit()


class Base(DeclarativeBase):
    def _repr(self, fields: dict[Any, Any]) -> str:
        """Helper for __repr__

        Sourced from https://stackoverflow.com/a/55749579 with slight modifications
        """
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f"{key}={field!r}")
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f"{key}=DetachedInstanceError")
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({', '.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


class DiscordPlayers(Base):
    __tablename__ = "discords_players"

    discord_id: Mapped[int] = mapped_column(ForeignKey("discord.id"), primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"), primary_key=True)
    main: Mapped[bool] = mapped_column(nullable=True)
    discord: Mapped["Discord"] = relationship(back_populates="players")
    player: Mapped["Player"] = relationship(back_populates="discords")

    def __repr__(self) -> str:
        return self._repr(
            fields=dict(
                discord_id=self.discord_id,
                player_id=self.player_id,
                main=self.main,
                discord=self.discord,
                player=self.player,
            )
        )

    # Used to guarantee only a single `main` player ID but unlimited sponsored
    __table_args__ = (
        Index(
            "only_one_main",
            "main",
            "discord_id",
            unique=True,
            sqlite_where=(~~main),
        ),
    )


class Discord(Base):
    """Tracks Discord user accounts"""

    __tablename__ = "discord"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_name: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(tz=timezone.utc))
    modified_at: Mapped[datetime] = mapped_column(
        default=datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
    )
    players: Mapped[list[DiscordPlayers]] = relationship(back_populates="discord")
    patreon: Mapped[Optional["Patreon"]] = relationship(back_populates="discord")

    def __repr__(self) -> str:
        return self._repr(
            fields=dict(
                id=self.id,
                discord_name=self.discord_name,
                patreon=self.patreon,
                num_players=len(self.players),
            )
        )


class Player(Base):
    """Tracks CRCON Players"""

    __tablename__ = "player"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(tz=timezone.utc))
    modified_at: Mapped[datetime] = mapped_column(
        default=datetime.now(tz=timezone.utc),
        onupdate=datetime.now(tz=timezone.utc),
    )

    discords: Mapped[list[DiscordPlayers]] = relationship(back_populates="player")

    def __repr__(self) -> str:
        return self._repr(
            fields=dict(
                id=self.id, player_id=self.player_id, num_discords=len(self.discords)
            )
        )


class Patreon(Base):
    """Tracks Patreon accounts"""

    __tablename__ = "patreon"

    id: Mapped[int] = mapped_column(primary_key=True)
    patreon_id: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(tz=timezone.utc))
    modified_at: Mapped[datetime] = mapped_column(
        default=datetime.now(tz=timezone.utc),
        onupdate=datetime.now(tz=timezone.utc),
    )

    discord_id: Mapped[int] = mapped_column(ForeignKey("discord.id"))
    discord: Mapped[Discord] = relationship(back_populates="patreon")

    def __repr__(self) -> str:
        return self._repr(
            fields=dict(
                id=self.id, patreon_id=self.patreon_id, discord_id=self.discord_id
            )
        )


Base.metadata.create_all(engine)

if __name__ == "__main__":
    with enter_session() as session:
        d1 = Discord(discord_name="discord#0")
        d2 = Discord(discord_name="discord#1")

        pat1 = Patreon(patreon_id="1234")
        pat1.discord = d1

        p1 = Player(player_id="1234")
        p2 = Player(player_id="4321")
        p3 = Player(player_id="5678")
        p4 = Player(player_id="8765")

        d1_p1 = DiscordPlayers(main=True, discord=d1, player=p1)
        d1_p2 = DiscordPlayers(main=False, discord=d1, player=p2)
        d1_p3 = DiscordPlayers(main=False, discord=d1, player=p3)

        session.add_all([d1, d2, p1, p2])
