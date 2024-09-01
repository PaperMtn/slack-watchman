# syntax=docker/dockerfile:1

#FROM python:3.12-slim-bullseye
#WORKDIR /opt/slack-watchman
#COPY . /opt/slack-watchman
#RUN pip install poetry
#ENV PYTHONPATH=/opt/slack-watchman \
#    SLACK_WATCHMAN_TOKEN="" \
#    SLACK_WATCHMAN_COOKIE="" \
#    SLACK_WATCHMAN_URL=""
#RUN poetry config virtualenvs.create false && \
#    poetry install --no-dev && \
#    chmod -R 700 . && \
#    poetry build && \
#    pip install dist/*.whl
#STOPSIGNAL SIGINT
#WORKDIR /opt/slack-watchman
#ENTRYPOINT ["slack-watchman"]

# syntax=docker/dockerfile:1
FROM python:3.12-slim-bullseye AS builder
WORKDIR /opt/slack-watchman
COPY . .
RUN pip install poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev && \
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