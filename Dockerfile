# syntax=docker/dockerfile:1
FROM python:3.12-slim-bullseye AS builder
WORKDIR /opt/slack-watchman
COPY . .
RUN pip install poetry
RUN poetry config virtualenvs.create false && \
    poetry install --only main && \
    poetry build

FROM python:3.12-slim-bullseye
WORKDIR /opt/slack-watchman
COPY --from=builder /opt/slack-watchman/dist/*.whl /opt/slack-watchman/dist/
COPY --from=builder /opt/slack-watchman/pyproject.toml /opt/slack-watchman/poetry.lock /opt/slack-watchman/
ENV PYTHONPATH=/opt/slack-watchman \
    SLACK_WATCHMAN_TOKEN="" \
    SLACK_WATCHMAN_COOKIE="" \
    SLACK_WATCHMAN_URL=""
RUN pip install dist/*.whl && \
    chmod -R 700 .
STOPSIGNAL SIGINT
ENTRYPOINT ["slack-watchman"]