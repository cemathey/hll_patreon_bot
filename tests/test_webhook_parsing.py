from logging import getLogger

import pytest

from hll_patreon_bot.patreon_webhook.types import PatreonMemberWH, PatreonPledgeWH
from hll_patreon_bot.patreon_webhook.utils import (
    parse_patreon_member_webhook,
    parse_patreon_pledge_webhook,
)

# from hll_patreon_bot.patreon_webhook


logger = getLogger(__name__)


def test_parse_patreon_member_webhook():
    raw_data = {
        "data": {
            "attributes": {
                "campaign_lifetime_support_cents": 5000,
                "currently_entitled_amount_cents": 0,
                "email": "eric58391@gmail.com",
                "full_name": "Christopher Mathey",
                "is_follower": False,
                "is_free_trial": False,
                "last_charge_date": "2024-01-31T20:46:10.000+00:00",
                "last_charge_status": "Pending",
                "lifetime_support_cents": 5000,
                "next_charge_date": "2024-03-01T00:00:00.000+00:00",
                "note": "",
                "patron_status": "active_patron",
                "pledge_cadence": 1,
                "pledge_relationship_start": "2022-03-07T07:34:51.725+00:00",
                "will_pay_amount_cents": 500,
            },
            "id": "52c7b310-8d73-4ce8-bfba-ef1caa58eb4e",
            "relationships": {
                "address": {"data": None},
                "campaign": {
                    "data": {"id": "8290127", "type": "campaign"},
                    "links": {
                        "related": "https://www.patreon.com/api/oauth2/v2/campaigns/8290127"
                    },
                },
                "currently_entitled_tiers": {
                    "data": [{"id": "10623881", "type": "tier"}]
                },
                "user": {
                    "data": {"id": "719414", "type": "user"},
                    "links": {
                        "related": "https://www.patreon.com/api/oauth2/v2/user/719414"
                    },
                },
            },
            "type": "member",
        },
        "included": [
            {
                "attributes": {
                    "created_at": "2022-02-26T14:51:33.000+00:00",
                    "creation_name": "creating a Gaming Community",
                    "discord_server_id": "722918218305503282",
                    "google_analytics_id": None,
                    "has_rss": False,
                    "has_sent_rss_notify": False,
                    "image_small_url": "https://c10.patreonusercontent.com/4/patreon-media/p/campaign/8290127/65187d90ef454092907f9d5423330d9a/eyJ3IjoxOTIwLCJ3ZSI6MX0%3D/2.png?token-time=1707004800&token-hash=HHpDNlEd7jjFS8PIdHAE9kpw5ct4m0l969vVlMz0L94%3D",
                    "image_url": "https://c10.patreonusercontent.com/4/patreon-media/p/campaign/8290127/65187d90ef454092907f9d5423330d9a/eyJ3IjoxOTIwLCJ3ZSI6MX0%3D/2.png?token-time=1707004800&token-hash=HHpDNlEd7jjFS8PIdHAE9kpw5ct4m0l969vVlMz0L94%3D",
                    "is_charged_immediately": True,
                    "is_monthly": True,
                    "is_nsfw": False,
                    "main_video_embed": None,
                    "main_video_url": None,
                    "one_liner": None,
                    "patron_count": 259,
                    "pay_per_name": "month",
                    "pledge_url": "/checkout/BEERHaus",
                    "published_at": "2022-02-26T15:11:37.000+00:00",
                    "rss_artwork_url": None,
                    "rss_feed_title": None,
                    "summary": "Saucymuffin's [BEER] haus and Squidd Cafe is a Hell Let Loose public server created by\u00a0 Saucymuffin, FreshBakedGoods, Squiddstv, and Raz_Bora in order to create one of the most popular servers in the HLL Community.\u00a0 Together we have stepped up to create a top ranked server by Creators for Creators and their communities.\u00a0 By pledging a $5 monthly donation you will receive VIP access to the server to skip the queue so you can play with the TOP Hell Let Loose streamers and youtubers!<br><br>See you on the battlefield!\u00a0",
                    "thanks_embed": None,
                    "thanks_msg": None,
                    "thanks_video_url": None,
                    "url": "https://www.patreon.com/BEERHaus",
                    "vanity": "BEERHaus",
                },
                "id": "8290127",
                "type": "campaign",
            },
            {
                "attributes": {
                    "about": "",
                    "created": "2015-04-22T22:26:37.000+00:00",
                    "first_name": "Christopher",
                    "full_name": "Christopher Mathey",
                    "hide_pledges": False,
                    "image_url": "https://c8.patreon.com/3/200/719414",
                    "is_creator": False,
                    "last_name": "Mathey",
                    "like_count": 0,
                    "social_connections": {
                        "discord": {"url": None, "user_id": "296385262794178570"},
                        "facebook": None,
                        "google": None,
                        "instagram": None,
                        "reddit": None,
                        "spotify": None,
                        "spotify_open_access": None,
                        "tiktok": None,
                        "twitch": None,
                        "twitter": None,
                        "vimeo": None,
                        "youtube": None,
                    },
                    "thumb_url": "https://c8.patreon.com/3/200/719414",
                    "url": "https://www.patreon.com/user?u=719414",
                    "vanity": None,
                },
                "id": "719414",
                "type": "user",
            },
            {
                "attributes": {
                    "amount_cents": 0,
                    "created_at": "2023-10-12T23:34:36.141+00:00",
                    "description": "",
                    "discord_role_ids": None,
                    "edited_at": "2023-10-12T23:34:36.141+00:00",
                    "image_url": None,
                    "patron_count": 0,
                    "post_count": 0,
                    "published": True,
                    "published_at": "2023-10-12T23:34:36.141+00:00",
                    "remaining": None,
                    "requires_shipping": False,
                    "title": "Free",
                    "unpublished_at": None,
                    "url": "/checkout/BEERHaus?rid=10623881",
                    "user_limit": None,
                },
                "id": "10623881",
                "type": "tier",
            },
        ],
        "links": {
            "self": "https://www.patreon.com/api/oauth2/v2/members/52c7b310-8d73-4ce8-bfba-ef1caa58eb4e"
        },
    }
    res = parse_patreon_member_webhook(raw_data)


@pytest.mark.parametrize(
    "data", [({}), {"data": {"attributes": "2024-01-31T20:46:10.000+00:00"}}]
)
def test_parse_patreon_member_webhook_exceptions(data):
    with pytest.raises(KeyError):
        parse_patreon_member_webhook(data)


def test_parse_patreon_pledge_webhook():
    raw_data = {
        "data": {
            "attributes": {
                "campaign_lifetime_support_cents": 5000,
                "currently_entitled_amount_cents": 500,
                "email": "eric58391@gmail.com",
                "full_name": "Christopher Mathey",
                "is_follower": False,
                "is_free_trial": False,
                "last_charge_date": "2024-01-31T20:46:10.000+00:00",
                "last_charge_status": "Pending",
                "lifetime_support_cents": 5000,
                "next_charge_date": "2024-03-01T00:00:00.000+00:00",
                "note": "",
                "patron_status": "active_patron",
                "pledge_cadence": 1,
                "pledge_relationship_start": "2022-03-07T07:34:51.725+00:00",
                "will_pay_amount_cents": 500,
            },
            "id": "52c7b310-8d73-4ce8-bfba-ef1caa58eb4e",
            "relationships": {
                "address": {"data": None},
                "campaign": {
                    "data": {"id": "8290127", "type": "campaign"},
                    "links": {
                        "related": "https://www.patreon.com/api/oauth2/v2/campaigns/8290127"
                    },
                },
                "currently_entitled_tiers": {
                    "data": [{"id": "8348592", "type": "tier"}]
                },
                "user": {
                    "data": {"id": "719414", "type": "user"},
                    "links": {
                        "related": "https://www.patreon.com/api/oauth2/v2/user/719414"
                    },
                },
            },
            "type": "member",
        },
        "included": [
            {
                "attributes": {
                    "created_at": "2022-02-26T14:51:33.000+00:00",
                    "creation_name": "creating a Gaming Community",
                    "discord_server_id": "722918218305503282",
                    "google_analytics_id": None,
                    "has_rss": False,
                    "has_sent_rss_notify": False,
                    "image_small_url": "https://c10.patreonusercontent.com/4/patreon-media/p/campaign/8290127/65187d90ef454092907f9d5423330d9a/eyJ3IjoxOTIwLCJ3ZSI6MX0%3D/2.png?token-time=1707004800&token-hash=HHpDNlEd7jjFS8PIdHAE9kpw5ct4m0l969vVlMz0L94%3D",
                    "image_url": "https://c10.patreonusercontent.com/4/patreon-media/p/campaign/8290127/65187d90ef454092907f9d5423330d9a/eyJ3IjoxOTIwLCJ3ZSI6MX0%3D/2.png?token-time=1707004800&token-hash=HHpDNlEd7jjFS8PIdHAE9kpw5ct4m0l969vVlMz0L94%3D",
                    "is_charged_immediately": True,
                    "is_monthly": True,
                    "is_nsfw": False,
                    "main_video_embed": None,
                    "main_video_url": None,
                    "one_liner": None,
                    "patron_count": 259,
                    "pay_per_name": "month",
                    "pledge_url": "/checkout/BEERHaus",
                    "published_at": "2022-02-26T15:11:37.000+00:00",
                    "rss_artwork_url": None,
                    "rss_feed_title": None,
                    "summary": "Saucymuffin's [BEER] haus and Squidd Cafe is a Hell Let Loose public server created by\u00a0 Saucymuffin, FreshBakedGoods, Squiddstv, and Raz_Bora in order to create one of the most popular servers in the HLL Community.\u00a0 Together we have stepped up to create a top ranked server by Creators for Creators and their communities.\u00a0 By pledging a $5 monthly donation you will receive VIP access to the server to skip the queue so you can play with the TOP Hell Let Loose streamers and youtubers!<br><br>See you on the battlefield!\u00a0",
                    "thanks_embed": None,
                    "thanks_msg": None,
                    "thanks_video_url": None,
                    "url": "https://www.patreon.com/BEERHaus",
                    "vanity": "BEERHaus",
                },
                "id": "8290127",
                "type": "campaign",
            },
            {
                "attributes": {
                    "about": "",
                    "created": "2015-04-22T22:26:37.000+00:00",
                    "first_name": "Christopher",
                    "full_name": "Christopher Mathey",
                    "hide_pledges": False,
                    "image_url": "https://c8.patreon.com/3/200/719414",
                    "is_creator": False,
                    "last_name": "Mathey",
                    "like_count": 0,
                    "social_connections": {
                        "discord": {"url": None, "user_id": "296385262794178570"},
                        "facebook": None,
                        "google": None,
                        "instagram": None,
                        "reddit": None,
                        "spotify": None,
                        "spotify_open_access": None,
                        "tiktok": None,
                        "twitch": None,
                        "twitter": None,
                        "vimeo": None,
                        "youtube": None,
                    },
                    "thumb_url": "https://c8.patreon.com/3/200/719414",
                    "url": "https://www.patreon.com/user?u=719414",
                    "vanity": None,
                },
                "id": "719414",
                "type": "user",
            },
            {
                "attributes": {
                    "amount_cents": 500,
                    "created_at": "2022-02-26T15:04:10.507+00:00",
                    "description": "A simple $5 monthly Donation that goes toward server upkeep and maintenance which garuntees you VIP white listing for the Saucymuffin's [BEER] Haus and Squidd Cafe server.",
                    "discord_role_ids": ["947148212534386738"],
                    "edited_at": "2022-02-26T15:11:28.288+00:00",
                    "image_url": None,
                    "patron_count": 270,
                    "post_count": 1,
                    "published": True,
                    "published_at": "2022-02-26T15:11:28.274+00:00",
                    "remaining": None,
                    "requires_shipping": False,
                    "title": "VIP Member",
                    "unpublished_at": None,
                    "url": "/checkout/BEERHaus?rid=8348592",
                    "user_limit": None,
                },
                "id": "8348592",
                "type": "tier",
            },
        ],
        "links": {
            "self": "https://www.patreon.com/api/oauth2/v2/members/52c7b310-8d73-4ce8-bfba-ef1caa58eb4e"
        },
    }
    res = parse_patreon_pledge_webhook(raw_data)


@pytest.mark.parametrize(
    "data", [({}), {"data": {"attributes": "2024-01-31T20:46:10.000+00:00"}}]
)
def test_parse_patreon_pledge_webhook_exceptions(data):
    with pytest.raises(KeyError):
        parse_patreon_pledge_webhook(data)
