#!/usr/bin/env bash
set -e
set -x

if [ ! -d "./logs" ]
then
    echo "Creating logs directory"
    mkdir ./logs
fi

PYTHONPATH=hll_patreon_bot poetry run hypercorn --log-file /code/logs/webserver.log --bind 0.0.0.0:8888 hll_patreon_bot.patreon_webhook.webhook_listener:app