# syntax=docker/dockerfile:1
ARG slack_watchman_token
FROM python:3.10
COPY . /opt/slack-watchman
WORKDIR /opt/slack-watchman
ENV PYTHONPATH=/opt/slack-watchman SLACK_WATCHMAN_TOKEN="${slack_watchman_token}" SLACK_WATCHMAN_COOKIE="" SLACK_WATCHMAN_URL=""
RUN pip3 install -r requirements.txt build && \
    chmod -R 700 . && \
    python3 -m build && \
    python3 -m pip install dist/*.whl
STOPSIGNAL SIGINT
WORKDIR /opt/slack-watchman
ENTRYPOINT ["slack-watchman"]
