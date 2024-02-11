import locale
import operator
from datetime import datetime, timezone
from pprint import pprint

import discord
import httpx
from bot.constants import PATREON_ACCESS_TOKEN, PATREON_CAMPAIGN_ID, PATREON_HOST_NAME
from bot.models import enter_session
from bot.utils import (
    get_set_discord_record,
    get_set_patreon_record,
    link_patreon_to_discord,
    one_or_none,
    unlink_patreon_from_discord,
)
from cachetools import TTLCache, cached, cachedmethod
from discord.commands import ApplicationContext
from discord.ext import commands
from patreon_v2 import typedefs as patreon_api_types
from patreon_v2.async_api import AsyncAPI as PatreonAPI

locale.setlocale(locale.LC_ALL, "")


def create_patreon_search_embed(
    email: str | None = None,
    patreon_id: str | None = None,
    name: str | None = None,
    notes: str | None = None,
):
    embed = discord.Embed()
    embed.title = "Searching Patreon, this may take 5-10 seconds"
    embed.add_field(name="Email", value=email if email else "", inline=False)
    embed.add_field(
        name="Patreon ID", value=patreon_id if patreon_id else "", inline=False
    )
    embed.add_field(name="Name", value=name if name else "", inline=False)
    embed.add_field(name="Notes", value=notes if notes else "", inline=False)

    embed.timestamp = datetime.now(tz=timezone.utc)
    return embed


def create_pledge_history_embed(
    pledge_histories: list[patreon_api_types.PledgeEvent],
) -> discord.Embed:
    embed = discord.Embed()

    embed.title = "Pledge History (up to last 5)"
    for p in pledge_histories:
        embed.add_field(
            name="Date:", value=f"<t:{int(p.date.timestamp())}:f>", inline=True
        )
        embed.add_field(
            name="Amount: ",
            value=(
                locale.currency(p.amount_cents / 100, symbol=True, grouping=True)
                if p
                else ""
            ),
            inline=True,
        )
        embed.add_field(name="\u200B", value="\u200B")  # newline
        # embed.add_field(name="\u200b", value="\u200b", inline=False)

    embed.timestamp = datetime.now(tz=timezone.utc)

    return embed


def create_patreon_embed(
    member: patreon_api_types.Member,
    user: patreon_api_types.User | None = None,
    tiers: dict[str, patreon_api_types.Tier] | None = None,
    pledge_histories: dict[str, patreon_api_types.PledgeEvent] | None = None,
) -> discord.Embed:
    embed = discord.Embed()

    embed.add_field(name="Patreon ID", value=member.id, inline=False)
    embed.add_field(
        name="Patreon User ID", value=member.user_id if member.user_id else ""
    )
    embed.add_field(name="Email", value=member.email if member.email else "")
    embed.add_field(name="Name", value=member.full_name if member.full_name else "")
    embed.add_field(
        name="Patron Status",
        value=(
            member.patron_status.value
            if member.patron_status and member.patron_status.value
            else ""
        ),
    )
    embed.add_field(
        name="Last Charge Status",
        value=(
            member.last_charge_status.value
            if member.last_charge_status and member.last_charge_status.value
            else ""
        ),
        inline=False,
    )
    embed.add_field(
        name="Last Charge (or attempted charge) Date",
        value=(
            f"<t:{int(member.last_charge_date.timestamp())}:f>"
            if member.last_charge_date
            else ""
        ),
    )
    embed.add_field(
        name="Next Charge Date",
        value=(
            f"<t:{int(member.next_charge_date.timestamp())}:f>"
            if member.next_charge_date
            else ""
        ),
        inline=False,
    )
    embed.add_field(
        name="Currently Entitled Amount",
        value=(
            locale.currency(
                member.currently_entitled_amount_cents / 100, symbol=True, grouping=True
            )
            if member.currently_entitled_amount_cents
            else ""
        ),
    )

    for tier in member.currently_entitled_tiers:
        t = tiers.get(tier, None) if tiers else None
        # print(f"{t=} {tier=}")
        embed.add_field(
            name="Tier: ", value=t.title if t and t.title else "", inline=False
        )
        # embed.add_field(
        #     name="Tier: ", value=t.description if t and t.description else ""
        # )

    embed.add_field(name="Patreon Notes", value=member.note if member.note else "")
    embed.timestamp = datetime.now(tz=timezone.utc)

    return embed


# def format_patreon_member_display(member: patreon_api_types.Member):
#     # TODO hammertyme this and use embeds/md for better formatting
#     return f"""
# Patreon ID: `{member.id}`
# email: `{member.email}`
# Name: `{member.full_name}`
# Patron Status: `{member.patron_status.value if member.patron_status else None}`
# Last Charge Status: `{member.last_charge_status.value if member.last_charge_status else None}`
# Last Charge (or attempted charge) Date: `{member.last_charge_date}`
# Next Charge Date: `{member.next_charge_date}`
# Patreon Notes: `{member.note}`
# """


class Patreon(commands.Cog):
    def __init__(
        self, bot, acccess_token: str | None = None, base_url: str | None = None
    ) -> None:
        super().__init__()
        self.bot = bot
        self.api = PatreonAPI(
            access_token=acccess_token or PATREON_ACCESS_TOKEN,
            base_url=base_url or PATREON_HOST_NAME,
        )
        self.cache = TTLCache(maxsize=500, ttl=60)

    @cachedmethod(operator.attrgetter("cache"))
    async def fetch_members(self):
        members, related_objects = await self.api.get_campaign_members(
            campaign=PATREON_CAMPAIGN_ID, all_includes_all_fields=True, fetch_all=True
        )

        return members, related_objects

    @discord.slash_command(description="Show the user's status on Patreon")
    async def show_patreon(self, ctx: ApplicationContext, discord_user: discord.User):
        with enter_session() as session:
            discord_record = get_set_discord_record(
                session=session, discord_user_name=discord_user.name
            )

            if discord_record.patreon is None:
                await ctx.respond(f"No Patreon account found for {discord_user}")
            else:
                patreon_member, includes = await self.api.get_member(
                    member=discord_record.patreon.patreon_id
                )
                await ctx.respond(embed=create_patreon_embed(patreon_member))

    @discord.slash_command(
        description="Link (connect) a Discord account to a Patreon account"
    )
    async def link_patreon(
        self, ctx: ApplicationContext, discord_user: discord.User, patreon_id: str
    ):
        patreon_member, includes = await self.api.get_member(member=patreon_id)

        if patreon_member is None:
            await ctx.respond(f"No Patreon account found for {patreon_id=}")

        patreon_id_already_linked = False
        previous_linked_discord = None
        with enter_session() as session:
            (
                patreon_id_already_linked,
                previous_linked_discord,
            ) = link_patreon_to_discord(
                session=session,
                patreon_id=patreon_id,
                discord_name=discord_user.name,
            )

        if patreon_id_already_linked:
            await ctx.respond(
                f"Linked {discord_user} to {patreon_id=} (was previously linked to {previous_linked_discord})"
            )
        else:
            await ctx.respond(f"Linked {discord_user} to {patreon_id=}")

    @discord.slash_command(
        description="Unlink (disconnect) a Discord account from their Patreon account"
    )
    async def unlink_patreon(
        self, ctx: ApplicationContext, discord_user: discord.User, patreon_id: str
    ):
        with enter_session() as session:
            linked_patreon_id = unlink_patreon_from_discord(
                session=session, patreon_id=patreon_id, discord_name=discord_user.name
            )

            if linked_patreon_id is None:
                await ctx.respond(
                    f"{discord_user} does not have a Patreon record in the database"
                )
                return
            elif linked_patreon_id == patreon_id:
                await ctx.respond(f"Unlinked {discord_user} from {patreon_id}")
            else:
                await ctx.respond(
                    f"{discord_user} has patreon_id=`{linked_patreon_id}` linked not `{patreon_id}`, account **not unlinked**"
                )

    @discord.slash_command(description="Search Patreon for a specific identifier")
    # TODO: describe options
    async def search_patreon(
        self,
        ctx: ApplicationContext,
        email: str | None,
        patreon_id: str | None,
        # discord_id: str | None,
        name: str | None,
        notes: str | None,
    ):
        await ctx.respond(
            embed=create_patreon_search_embed(
                email=email, patreon_id=patreon_id, name=name, notes=notes
            )
        )

        found_email = None
        found_patreon_id = None
        possible_names: list[patreon_api_types.Member] = []

        # members, related_objects = await self.api.get_campaign_members(
        #     campaign=PATREON_CAMPAIGN_ID, all_includes_all_fields=True, fetch_all=True
        # )
        members, related_objects = await self.fetch_members()
        print(f"{len(members)=}")
        # pprint(related_objects)

        # https://www.patreon.com/api/pledge-events?filter[patron.id]=44516775&filter[escape_pagination]=true&include=subscription.null,pledge.campaign.null&fields[campaign]=pay_per_name&fields[subscription]=amount_cents&fields[pledge_event]=pledge_payment_status,payment_status,date,type,tier_title&fields[pledge]=amount_cents,currency,status,cadence&json-api-version=1.0&json-api-use-default-includes=false
        # https://www.patreon.com/api/members/cd68584c-cc42-4b3b-b7b7-1ea49b29df1a?include=reward%2Crecent_charges%2Cuser%2Crecent_charges.post%2Crecent_charges.campaign.null&fields[user]=full_name%2Cthumb_url%2Curl%2Cis_follower%2Cpatron_status&fields[campaign]=has_annual_pledge&fields[member]=pledge_relationship_start%2Cnote%2Ccan_be_messaged%2Cdiscord_vanity&fields[post]=title&fields[charge]=date%2Camount_cents%2Ccurrency%2Cstatus%2Cis_refundable%2Cpartial_annual_refund_data%2Cunderlying_charge_type%2Cunderlying_charge_id%2Csupported_period_start%2Csupported_period_end&json-api-use-default-includes=false&json-api-version=1.0

        if email:
            found_email = one_or_none(lambda x: x.email == email, members)

        if patreon_id:
            found_patreon_id = one_or_none(lambda x: x.id == patreon_id, members)

        name_chunks = name.split() if name else []
        possible_names = list(
            filter(
                lambda x: any(
                    chunk in x.full_name for chunk in name_chunks if x.full_name
                ),
                members,
            )
        )

        if found_email:
            tiers = {
                t.id: t
                for t in filter(
                    lambda x: x.id in found_email.currently_entitled_tiers,
                    related_objects.get(patreon_api_types.PatreonResourceType.tier, []),
                )
            }
            pledge_histories = [
                p
                for p in filter(
                    lambda x: x.id in found_email.pledge_history,
                    related_objects.get(
                        patreon_api_types.PatreonResourceType.pledge_event, []
                    ),
                )
            ]

            pledge_histories = list(
                reversed(sorted(pledge_histories, key=lambda p: p.date))
            )

            await ctx.respond(
                embeds=[
                    create_patreon_embed(found_email, tiers=tiers),
                    create_pledge_history_embed(pledge_histories=pledge_histories[:5]),
                ]
            )
        elif found_patreon_id:
            await ctx.respond(embed=create_patreon_embed(found_patreon_id))
        elif possible_names:
            await ctx.respond(f"Showing up to 5 matches by name: ")
            for poss_name in possible_names:
                await ctx.respond(embed=create_patreon_embed(poss_name))
        else:
            await ctx.respond(
                f"No patreon member (searched {len(members)} members) found."
            )


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Patreon(bot))  # add the cog to the bot
