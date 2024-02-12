#!/usr/bin/env bash
set -e
set -x

# Set the locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8  

if [ ! -d "./logs" ]
then
    echo "Creating logs directory"
    mkdir ./logs
fi


PYTHONPATH=hll_patreon_bot poetry run python -m uvicorn --host 0.0.0.0 --port 8888 hll_patreon_bot.patreon_webhook.webhook_listener:app