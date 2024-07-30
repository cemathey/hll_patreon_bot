import locale
from datetime import datetime, timezone

import discord
import httpx
from cachetools import TTLCache, cached, cachedmethod
from discord.commands import ApplicationContext
from discord.ext import commands
from loguru import logger

from hll_patreon_bot.bot.utils import discord_name_as_user, one_or_none, with_permission
from hll_patreon_bot.database.models import enter_session
from hll_patreon_bot.database.utils import (
    get_set_discord_record,
    link_patreon_to_discord,
    unlink_patreon_from_discord,
)
from hll_patreon_bot.integrations.patreon.patreon import (
    get_campaign_members,
    get_member,
)
from hll_patreon_bot.integrations.patreon.types import PatreonMember, PledgeHistory

locale.setlocale(locale.LC_ALL, "")


def create_patreon_search_embed(
    email: str | None = None,
    patreon_id: str | None = None,
    discord_user: discord.User | None = None,
    name: str | None = None,
    notes: str | None = None,
):
    embed = discord.Embed()
    embed.title = "Searching Patreon, this may take 5-10 seconds"
    embed.add_field(
        name="Discord", value=discord_user.name if discord_user else "", inline=False
    )
    embed.add_field(name="Email", value=email if email else "", inline=False)
    embed.add_field(
        name="Patreon ID", value=patreon_id if patreon_id else "", inline=False
    )
    embed.add_field(name="Name", value=name if name else "", inline=False)
    embed.add_field(name="Notes", value=notes if notes else "", inline=False)

    embed.timestamp = datetime.now(tz=timezone.utc)
    return embed


def create_pledge_history_embed(
    pledge_histories: list[PledgeHistory],
) -> discord.Embed:
    embed = discord.Embed()

    embed.title = "Pledge History (up to last 5)"
    for p in pledge_histories[:5]:
        embed.add_field(
            name="Date:", value=f"<t:{int(p['date'].timestamp())}:f>", inline=True
        )
        embed.add_field(
            name="Amount: ",
            value=(
                locale.currency(p["amount_cents"] / 100, symbol=True, grouping=True)
                if p
                else ""
            ),
            inline=True,
        )
        embed.add_field(name="Status", value=str(p["status"]), inline=True)

    embed.timestamp = datetime.now(tz=timezone.utc)

    return embed


def create_patreon_embed(
    member: PatreonMember,
    discord_user: discord.User | None = None,
) -> discord.Embed:
    embed = discord.Embed()

    if discord_user:
        embed.add_field(
            name="Discord",
            value=f"{discord_user.mention}",
        )

    embed.add_field(name="Patreon ID", value=member["id"], inline=False)
    embed.add_field(name="Email", value=member["email"])
    embed.add_field(name="Name", value=member["name"] if member["name"] else "")
    embed.add_field(
        name="Patron Status",
        value=member["patron_status"].value if member["patron_status"].value else "",
    )
    embed.add_field(
        name="Last Charge Status",
        value=(
            member["last_charge_status"].value
            if member["last_charge_status"].value
            else ""
        ),
        inline=False,
    )
    embed.add_field(
        name="Last Charge (or attempted charge) Date",
        value=(
            f"<t:{int(member['last_charge_date'].timestamp())}:f>"
            if member["last_charge_date"]
            else ""
        ),
    )
    embed.add_field(
        name="Next Charge Date",
        value=(
            f"<t:{int(member['next_charge_date'].timestamp())}:f>"
            if member["next_charge_date"]
            else ""
        ),
        inline=False,
    )
    embed.add_field(
        name="Currently Entitled Amount",
        value=(
            locale.currency(
                member["currently_entitled_amount_cents"] / 100,
                symbol=True,
                grouping=True,
            )
        ),
    )

    embed.add_field(
        name="Patreon Notes", value=member["note"] if member["note"] else ""
    )

    if member["thumb_url"]:
        embed.url = member["thumb_url"]

    embed.timestamp = datetime.now(tz=timezone.utc)

    # TODO: Include payment history

    return embed


class Patreon(commands.Cog):
    def __init__(
        self, bot, acccess_token: str | None = None, base_url: str | None = None
    ) -> None:
        super().__init__()
        self.bot = bot

    # TODO: Figure out how to cache these results
    # @cachedmethod(operator.attrgetter("cache"))
    async def fetch_members(self):
        async with httpx.AsyncClient() as client:
            # get_campaign_members yields successfully more populated dicts per page
            # so we can just take the last value when we're getting everyone
            async for members in get_campaign_members(client=client):
                pass

        return members

    @discord.slash_command(description="Show the user's status on Patreon")
    async def show_patreon(self, ctx: ApplicationContext, discord_user: discord.User):
        if not with_permission(ctx):
            return

        with enter_session() as session:
            discord_record = get_set_discord_record(
                session=session, discord_user_name=discord_user.name
            )

            if discord_record.patreon is None:
                await ctx.respond(
                    f"No Patreon account found for {discord_user.mention}"
                )
            else:
                async with httpx.AsyncClient() as client:
                    patreon_member = await get_member(
                        client=client, member_id=discord_record.patreon.patreon_id
                    )

                if patreon_member:
                    patreon_embed = create_patreon_embed(
                        member=patreon_member, discord_user=discord_user
                    )
                    pledge_embed = create_pledge_history_embed(
                        pledge_histories=patreon_member["pledge_history"]
                    )
                    await ctx.respond(embeds=[patreon_embed, pledge_embed])

    @discord.slash_command(description="Link a Discord account to a Patreon account")
    async def link_patreon(
        self, ctx: ApplicationContext, discord_user: discord.User, patreon_id: str
    ):
        if not with_permission(ctx):
            return

        async with httpx.AsyncClient() as client:
            patreon_member = await get_member(client=client, member_id=patreon_id)

        if patreon_member is None:
            await ctx.respond(f"No Patreon account found for Patreon ID `{patreon_id}`")
            return

        previous_linked_discord = None
        with enter_session() as session:
            previous_linked_discord = link_patreon_to_discord(
                session=session,
                patreon_id=patreon_id,
                discord_name=discord_user.name,
            )

        if previous_linked_discord and previous_linked_discord != discord_user.name:
            previous_user = discord_name_as_user(
                discord_name=previous_linked_discord, members=ctx.guild.members
            )
            await ctx.respond(
                f"Linked {discord_user.mention} to Patreon ID `{patreon_id}` (was previously linked to {previous_user.mention if previous_user else previous_linked_discord})"
            )
        elif previous_linked_discord == discord_user.name:
            await ctx.respond(
                f"{discord_user.mention} was already linked to `{patreon_id}`"
            )
        else:
            await ctx.respond(
                f"Linked {discord_user.mention} to Patreon ID `{patreon_id}`"
            )

    @discord.slash_command(
        description="Unlink a Discord account from their Patreon account"
    )
    async def unlink_patreon(self, ctx: ApplicationContext, discord_user: discord.User):
        if not with_permission(ctx):
            return

        with enter_session() as session:
            linked_patreon_id = unlink_patreon_from_discord(
                session=session, discord_name=discord_user.name
            )

            if linked_patreon_id is None:
                await ctx.respond(
                    f"{discord_user.mention} does not have a Patreon record in the database"
                )
                return
            else:
                await ctx.respond(
                    f"{discord_user.mention} unlinked from `{linked_patreon_id}`"
                )

    @discord.slash_command(description="Search Patreon for a specific identifier")
    # TODO: describe options
    async def search_patreon(
        self,
        ctx: ApplicationContext,
        email: str | None,
        patreon_id: str | None,
        discord_user: discord.User | None,
        name: str | None,
        notes: str | None,
    ):
        if not with_permission(ctx):
            return

        await ctx.respond(
            embed=create_patreon_search_embed(
                email=email,
                patreon_id=patreon_id,
                discord_user=discord_user,
                name=name,
                notes=notes,
            )
        )

        found_email: PatreonMember | None = None
        found_patreon_id: PatreonMember | None = None
        found_discord_user: PatreonMember | None = None
        possible_names: list[PatreonMember] = []
        possible_notes: list[PatreonMember] = []

        # members = await self.fetch_members()
        async with httpx.AsyncClient() as client:
            # get_campaign_members yields successfully more populated dicts per page
            # so we can just take the last value when we're getting everyone
            msg: discord.WebhookMessage = await ctx.respond(f"Fetching members")
            async for members in get_campaign_members(client=client):
                await msg.edit(f"Fetching members ({len(members)} found so far)")
                print(f"Fetching members ({len(members)} found so far)")

        # TODO: do we have exactly 500 members? seems unlikely, are we being capped or what
        # logger.warning(f"{json.dumps(members)}")
        print(f"{len(members)=}")
        for key, value in members.items():
            # print(f"members[0]={value}")
            break

        # https://www.patreon.com/api/pledge-events?filter[patron.id]=44516775&filter[escape_pagination]=true&include=subscription.null,pledge.campaign.null&fields[campaign]=pay_per_name&fields[subscription]=amount_cents&fields[pledge_event]=pledge_payment_status,payment_status,date,type,tier_title&fields[pledge]=amount_cents,currency,status,cadence&json-api-version=1.0&json-api-use-default-includes=false
        # https://www.patreon.com/api/members/cd68584c-cc42-4b3b-b7b7-1ea49b29df1a?include=reward%2Crecent_charges%2Cuser%2Crecent_charges.post%2Crecent_charges.campaign.null&fields[user]=full_name%2Cthumb_url%2Curl%2Cis_follower%2Cpatron_status&fields[campaign]=has_annual_pledge&fields[member]=pledge_relationship_start%2Cnote%2Ccan_be_messaged%2Cdiscord_vanity&fields[post]=title&fields[charge]=date%2Camount_cents%2Ccurrency%2Cstatus%2Cis_refundable%2Cpartial_annual_refund_data%2Cunderlying_charge_type%2Cunderlying_charge_id%2Csupported_period_start%2Csupported_period_end&json-api-use-default-includes=false&json-api-version=1.0

        if email:
            found_email = one_or_none(lambda x: x["email"] == email, members.values())

        if patreon_id:
            found_patreon_id = members.get(patreon_id)

        if discord_user:
            for member in members.values():
                if member["email"] == "eric58391@gmail.com":
                    print(f"{member['email']} id={member['discord_user_id']}")
            found_discord_user = one_or_none(
                lambda x: x["discord_user_id"] == discord_user.id, members.values()
            )

        if notes:
            for member in members.values():
                if notes in member["note"]:
                    possible_notes.append(member)

        name_chunks = name.split() if name else []
        possible_names = list(
            filter(
                lambda x: any(chunk in x["name"] for chunk in name_chunks),
                members.values(),
            )
        )

        # TODO: include pledge history again
        if found_email:
            # tiers = {
            #     t.id: t
            #     for t in filter(
            #         lambda x: x.id in found_email.currently_entitled_tiers,
            #         related_objects.get(patreon_api_types.PatreonResourceType.tier, []),
            #     )
            # }
            # pledge_histories = [
            #     p
            #     for p in filter(
            #         lambda x: x.id in found_email.pledge_history,
            #         related_objects.get(
            #             patreon_api_types.PatreonResourceType.pledge_event, []
            #         ),
            #     )
            # ]

            # pledge_histories = list(
            #     reversed(sorted(pledge_histories, key=lambda p: p.date))
            # )

            await ctx.respond(
                embeds=[
                    create_patreon_embed(found_email),
                    create_pledge_history_embed(
                        pledge_histories=found_email["pledge_history"]
                    ),
                ]
            )
        elif found_patreon_id:
            await ctx.respond(embed=create_patreon_embed(found_patreon_id))
        elif found_discord_user:
            user = discord.utils.get(
                ctx.guild.members, id=found_discord_user["discord_user_id"]
            )
            await ctx.respond(
                embed=create_patreon_embed(found_discord_user, discord_user=user)
            )
        elif possible_names:
            await ctx.respond(f"Showing up to 5 matches by name: ")
            for poss_name in possible_names:
                await ctx.respond(embed=create_patreon_embed(poss_name))
        elif possible_notes:
            await ctx.respond(f"Showing up to 5 matches by notes:")
            for note in possible_notes:
                await ctx.respond(embed=create_patreon_embed(note))
        else:
            await ctx.respond(
                f"No patreon member (searched {len(members)} members) found."
            )


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Patreon(bot))  # add the cog to the bot
