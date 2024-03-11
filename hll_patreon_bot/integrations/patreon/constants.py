from typing import Final

MEMBER_BY_ID_URL: Final = "https://www.patreon.com/api/oauth2/v2/members/{member_id}"
MEMBER_BY_ID_PARAMS: Final = {
    "include": "campaign,address,currently_entitled_tiers,user",
    "fields[campaign]": "pledge_url,pay_per_name,thanks_embed,google_analytics_id,is_charged_immediately,created_at,thanks_video_url,has_sent_rss_notify,summary,discord_server_id,main_video_embed,main_video_url,image_small_url,rss_artwork_url,thanks_msg,has_rss,show_earnings,url,one_liner,rss_feed_title,image_url,vanity,is_nsfw,published_at,is_monthly,patron_count,creation_name",
    "fields[member]": "lifetime_support_cents,pledge_relationship_start,currently_entitled_amount_cents,next_charge_date,patron_status,campaign_lifetime_support_cents,pledge_cadence,is_follower,last_charge_date,full_name,note,will_pay_amount_cents,last_charge_status,email",
    "fields[tier]": "discord_role_ids,requires_shipping,remaining,post_count,url,created_at,image_url,title,user_limit,amount_cents,unpublished_at,published_at,edited_at,description,patron_count",
    "fields[address]": "postal_code,state,city,created_at,phone_number,line_2,addressee,line_1,country",
    "fields[user]": "about,last_name,like_count,can_see_nsfw,url,social_connections,image_url,first_name,created,hide_pledges,vanity,full_name,is_email_verified,email,thumb_url",
    "fields[pledge-event]": "payment_status,type,date,currency_code,tier_id,amount_cents,tier_title",
}

CAMPAIGN_MEMBERS_URL: Final = (
    "https://www.patreon.com/api/oauth2/v2/campaigns/{campaign_id}/members"
)
CAMPAIGN_MEMBERS_PARAMS: Final = {
    "include": "pledge_history",
    "include": "campaign,address,currently_entitled_tiers,user,pledge_history",
    "fields[user]": "url,full_name,image_url,first_name,email,thumb_url,about,can_see_nsfw,hide_pledges,is_email_verified,like_count,vanity,social_connections,last_name,created",
    "fields[address]": "phone_number,state,line_1,line_2,country,postal_code,addressee,city,created_at",
    "fields[member]": "full_name,email,next_charge_date,last_charge_status,last_charge_date,pledge_cadence,note,will_pay_amount_cents,lifetime_support_cents,pledge_relationship_start,campaign_lifetime_support_cents,currently_entitled_amount_cents,is_follower,patron_status",
    "fields[tier]": "url,image_url,unpublished_at,title,amount_cents,description,requires_shipping,edited_at,user_limit,published_at,created_at,post_count,patron_count,remaining,discord_role_ids",
    "fields[pledge-event]": "payment_status,type,date,currency_code,tier_id,amount_cents,tier_title",
    "fields[campaign]": "url,image_url,show_earnings,discord_server_id,thanks_embed,pledge_url,thanks_msg,image_small_url,google_analytics_id,pay_per_name,is_nsfw,main_video_url,published_at,one_liner,thanks_video_url,is_charged_immediately,creation_name,has_sent_rss_notify,has_rss,rss_feed_title,main_video_embed,summary,rss_artwork_url,is_monthly,vanity,created_at,patron_count",
}
