FROM python:3.11-alpine as base

ARG UID="500"
ARG GID="500"

WORKDIR /app

COPY amcrest2mqtt /app

RUN addgroup --system -g $GID appgroup && \
	adduser --system --uid $UID -G appgroup appuser && \
	chown -R appuser:appgroup /app

RUN apk add --no-cache curl
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN cp /root/.local/bin/poetry /usr/local/bin/

WORKDIR /app/amcrest2mqtt
RUN poetry config virtualenvs.create false && \
	poetry install --only main --no-interaction --no-ansi

USER appuser
CMD [ "python", "main.py" ]
