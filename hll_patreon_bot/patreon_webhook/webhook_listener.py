import asyncio
import json
import os
from logging import getLogger
from pprint import pprint
from typing import Callable

import aiohttp
import discord
import httpx
from bot.constants import API_KEY_FORMAT, CRCON_API_KEY
from patreon_webhook.actions import lookup_action
from patreon_webhook.constants import PATREON_TRIGGER_DELIMITER
from patreon_webhook.discord import lookup_action_embed
from patreon_webhook.types import (
    PatreonTriggerAction,
    PatreonTriggerResource,
    PatreonWebhook,
)
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

logger = getLogger("uvicorn")

# CLIENT: httpx.AsyncClient | None = None


# def get_client():
#     global CLIENT

#     if CLIENT is None:
#         CLIENT = httpx.AsyncClient()


async def raise_on_4xx_5xx(response):
    response.raise_for_status()


async def webhook(request: Request):
    headers = {"Authorization": API_KEY_FORMAT.format(api_key=CRCON_API_KEY)}
    wh = discord.Webhook.from_url(
        url=os.getenv("FORWARD_WEBHOOK", ""),
        session=aiohttp.ClientSession(),
    )

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

    async with httpx.AsyncClient(
        headers=headers, event_hooks={"response": [raise_on_4xx_5xx]}
    ) as client:
        await lookup_action(event=wh_type, client=client, data=data)
        embed = lookup_action_embed(event=wh_type, data=data)
        await wh.send(embed=embed)

        # TODO: execute wh embed
        # return Response(status_code=400)

    return Response(status_code=200)


app = Starlette(debug=True, routes=[Route("/", webhook, methods=["POST"])])

if __name__ == "__main__":
    pass
