from datetime import datetime, timezone

from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

engine = create_engine("sqlite:///file:db.sqlite?mode=rwc&uri=true", echo=True)


class Base(DeclarativeBase):
    pass


class Discord(Base):
    __tablename__ = "discords"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(tz=timezone.utc))
    modified_at: Mapped[datetime] = mapped_column(
        onupdate=datetime.now(tz=timezone.utc)
    )

    players: Mapped[list["Player"]] = relationship(back_populates="discord")
    patreon: Mapped["Patreon"] = relationship(back_populates="discord")


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(tz=timezone.utc))
    modified_at: Mapped[datetime] = mapped_column(
        onupdate=datetime.now(tz=timezone.utc)
    )

    discord_id: Mapped[int] = mapped_column(ForeignKey("discords.id"))
    discord: Mapped[Discord] = relationship(back_populates="players")


class Patreon(Base):
    __tablename__ = "patreons"

    id: Mapped[int] = mapped_column(primary_key=True)
    patreon_id: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(tz=timezone.utc))
    modified_at: Mapped[datetime] = mapped_column(
        onupdate=datetime.now(tz=timezone.utc)
    )

    discord_id: Mapped[int] = mapped_column(ForeignKey("discords.id"))
    discord: Mapped[Discord] = relationship(back_populates="players")


Base.metadata.create_all(engine)
