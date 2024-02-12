#!/usr/bin/env bash
set -e
set -x

if [ ! -d "./logs" ]
then
    echo "Creating logs directory"
    mkdir ./logs
fi


PYTHONPATH=hll_patreon_bot poetry run python -m uvicorn --host 0.0.0.0 --port 8888 hll_patreon_bot.patreon_webhook.webhook_listener:app