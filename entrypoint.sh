#!/usr/bin/env bash
set -e
set -x

if [ ! -d "./logs" ]
then
    echo "Creating logs directory"
    mkdir ./logs
fi

if [ "$1" == 'web_server' ] 
then
    PYTHONPATH=hll_patreon_bot poetry run hypercorn --log-file /code/logs/webserver.log --bind 0.0.0.0:8888 hll_patreon_bot.patreon_webhook.webhook_listener:app
fi

if [ "$1" ==  'discord_bot' ]
then
    poetry run python -m hll_patreon_bot.bot.main
fi