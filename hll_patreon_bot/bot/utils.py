import locale
from typing import Callable, Iterable, TypeVar

import discord
from discord.commands import ApplicationContext
from discord.role import Role

from hll_patreon_bot.bot.constants import AUTHORIZED_DISCORD_ROLES

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


def cents_as_currency(cents: int) -> str:
    locale.setlocale(locale.LC_ALL, "")
    return locale.currency(cents / 100, symbol=True, grouping=True)
