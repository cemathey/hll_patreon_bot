# syntax=docker/dockerfile:1
FROM python:3.11-slim-buster
ARG APP_NAME=hll_patreon_bot

WORKDIR /code

# Set the locale
RUN apt update -y \
    && apt upgrade --no-install-recommends -y \ 
    locales
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8 

# Install poetry
RUN apt update -y \
    && apt upgrade --no-install-recommends -y \ 
    pipx \
    python3-venv
RUN pipx ensurepath
RUN pipx install poetry
ENV PATH="/root/.local/bin:$PATH"
COPY poetry.lock pyproject.toml ./
# Avoid poetry complaining about the wrong python version
RUN poetry env use /usr/local/bin/python
RUN poetry install --no-root

COPY ./${APP_NAME} ${APP_NAME}
COPY ./entrypoint.sh entrypoint.sh

RUN chmod +x entrypoint.sh
ENTRYPOINT [ "/code/entrypoint.sh" ]