# syntax=docker/dockerfile:1
FROM python:3.11-slim-buster

ARG APP_NAME=hll_patreon_bot

WORKDIR /code
RUN apt update -y \
    && apt upgrade --no-install-recommends -y \ 
    curl
    # uvicorn
    # build-essential
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root

COPY ./${APP_NAME} ${APP_NAME}
COPY ./entrypoint.sh entrypoint.sh

RUN chmod +x entrypoint.sh
ENTRYPOINT [ "/code/entrypoint.sh" ]