Campaign ID: `8290127`

Member ID: `52c7b310-8d73-4ce8-bfba-ef1caa58eb4e`

Pledge ID: `pledge_start:158942977`

Cursor URL: `https://www.patreon.com/api/oauth2/v2/campaigns/8290127/members?include=pledge_history&fields%5Bpledge-event%5D=payment_status%2Ctype%2Cdate%2Ccurrency_code%2Ctier_id%2Camount_cents%2Ctier_title&page%5Bcursor%5D=02Yd345R9rabN7V2eEIgOyI5kb`

Steps to reproduce:
1. Use the `https://www.patreon.com/api/oauth2/v2/campaigns/{campaign_id}/members` endpoint to pull campaign members with the pledge-history include and fields
2. The pledge history for myself shows a payment status of `null` for pledge ID `pledge_start:158942977`
3. Open the members search on the website for our campaign (`eric58391@gmail.com` will show me) `https://www.patreon.com/members?query=eric58391%40gmail.com`
4. Open my specific member page and view the payment history on the bottom right which shows paid, as well as click the `See all payment history link` at the bottom and it shows the pledge `Became a Patron`
5. Use the `https://www.patreon.com/api/pledge-events?filter[patron.id]=719414&filter[escape_pagination]=true&include=subscription.null%2Cpledge.campaign.null&fields[campaign]=pay_per_name&fields[subscription]=amount_cents&fields[pledge_event]=pledge_payment_status%2Cpayment_status%2Cdate%2Ctype%2Ctier_title&fields[pledge]=amount_cents%2Ccurrency%2Cstatus%2Ccadence&json-api-version=1.0&json-api-use-default-includes=false` URL (used in the UI, I got it out of the network tab in the developer tools when pulling up my member page)
6. The pledge ID in `undocumented.json` shows pledge ID of `158942977` in the includes as successfully paid, where as `api.json` shows that pledge `payment_status` as `null`