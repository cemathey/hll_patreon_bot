import json
import os
from contextlib import asynccontextmanager
from logging import getLogger

import aiohttp
import discord
import httpx
from patreon_webhook.actions import lookup_action, lookup_parser
from patreon_webhook.constants import PATREON_TRIGGER_DELIMITER
from patreon_webhook.discord import lookup_action_embed
from patreon_webhook.types import (
    PatreonTriggerAction,
    PatreonTriggerResource,
    PatreonWebhook,
)
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from hll_patreon_bot.bot.constants import API_KEY_FORMAT, CRCON_API_KEY

logger = getLogger("uvicorn")

CLIENT: httpx.AsyncClient | None = None
WEBHOOK: discord.Webhook | None = None


def get_client():
    global CLIENT

    if CLIENT is None:
        headers = {"Authorization": API_KEY_FORMAT.format(api_key=CRCON_API_KEY)}
        CLIENT = httpx.AsyncClient(
            headers=headers, event_hooks={"response": [raise_on_4xx_5xx]}
        )

    return CLIENT


async def raise_on_4xx_5xx(response):
    response.raise_for_status()


@asynccontextmanager
async def with_client():
    client = get_client()
    yield client
    await client.aclose()


def get_webhook() -> discord.Webhook:
    global WEBHOOK

    if WEBHOOK is None:
        WEBHOOK = discord.Webhook.from_url(
            url=os.getenv("FORWARD_WEBHOOK", ""),
            session=aiohttp.ClientSession(),
        )

    return WEBHOOK


async def webhook(request: Request):
    wh = get_webhook()

    if not CRCON_API_KEY:
        raise ValueError(f"{CRCON_API_KEY} must be set")

    event_header = request.headers["X-Patreon-Event"]
    # TODO: check signature w/ webhook secret
    signature = request.headers["X-Patreon-Signature"]

    chunks = event_header.split(PATREON_TRIGGER_DELIMITER)

    resource = None
    sub_resource = None
    action = None
    if len(chunks) == 2:
        resource, action = chunks
        wh_type = PatreonWebhook(
            resource=PatreonTriggerResource(resource),
            action=PatreonTriggerAction(action),
        )
    elif len(chunks) == 3:
        resource, sub_resource, action = chunks
        wh_type = PatreonWebhook(
            resource=PatreonTriggerResource(resource),
            sub_resource=PatreonTriggerResource(sub_resource),
            action=PatreonTriggerAction(action),
        )
    else:
        logger.error(f"{event_header=}")
        return Response(status_code=400)

    logger.info(f"{resource=} {sub_resource=} {action=}")
    logger.info(f"{signature=}")
    data = await request.json()

    logger.info(json.dumps(data))

    async with with_client() as client:
        parser = lookup_parser(event=wh_type)
        parsed_data = parser(data)
        await lookup_action(event=wh_type, client=client, data=parsed_data)
        embed = lookup_action_embed(event=wh_type, data=parsed_data)
        await wh.send(embed=embed)

        # TODO: execute wh embed
        # return Response(status_code=400)

    await wh.delete()
    return Response(status_code=200)


app = Starlette(debug=True, routes=[Route("/", webhook, methods=["POST"])])

if __name__ == "__main__":
    pass
