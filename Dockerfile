FROM python:3.13-alpine as base

ARG UID="500"
ARG GID="500"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

COPY amcrest2mqtt /app

RUN addgroup --system -g $GID appgroup && \
	adduser --system --uid $UID -G appgroup appuser && \
	chown -R appuser:appgroup /app

RUN apk add --no-cache curl
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app/amcrest2mqtt
RUN /opt/poetry/bin/poetry config virtualenvs.create false && \
	/opt/poetry/bin/poetry install --only main --no-interaction --no-ansi

USER appuser
CMD [ "python", "main.py" ]
