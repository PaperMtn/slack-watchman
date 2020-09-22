# Logging
Slack Watchman gives the following logging options:
- CSV
- Log file
- Stdout
- TCP stream

## CSV logging
CSV logging is the default logging option if no other output method is given at runtime.

Results for each search are output as CSV files in your current working directory.

## JSON formatted logging
All other logging options output their logs in JSON format. Here is an example:

```json
{"localtime": "2020-00-00 00:00:00,000", "level": "NOTIFY", "source": "Slack Watchman", "workspace": "Westeros Inc", "scope": "messages", "type": "Twitter API Tokens", "severity": "90", "detection": {"channel_name": "lannister_chat", "message_id": "abc123", "permalink": "https://...", "posted_by": "tywin.lannister", "text": "<https://api.twitter.com/oauth/authorize?oauth_token=xXxXxX>", "timestamp": "2020-00-00 00:00:00"}}
```
This should contain all of the information you require to ingest these logs into a SIEM, or other log analysis platform.


### File logging
File logging saves JSON formatted logs to a file.

The path where you want to output the file needs to be passed when running Slack Watchman. This can be done via the .conf file:
```yaml
slack_watchman:
  token: xoxp-xxxxxxxx
  logging:
    file_logging:
      path: /var/put_my_logs_here/
    json_tcp:
      host:
      port:
```
Or by setting your log path in the environment variable: `SLACK_WATCHMAN_LOG_PATH`

If file logging is selected as the output option, but no path is give, Slack Watchman defaults to the user's home directory.

The filename will be `slack_watchman.log`

Note: Slack Watchman does not handle the rotation of the file. You would need a solution such as logrotate for this.

### Stdout logging
Stdout logging sends JSON formatted logs to Stdout, for you to capture however you want.

### TCP stream logging
With this option, JSON formmatted logs are sent to a destination of your choosing via TCP

You will need to pass Slack Watchman a host and port to receive the logs, either via .conf file:

```yaml
slack_watchman:
  token: xoxp-xxxxxxxx
  logging:
    file_logging:
      path:
    json_tcp:
      host: localhost
      port: 9020
```
Or by setting the environment variables `SLACK_WATCHMAN_HOST` and `SLACK_WATCHMAN_PORT`
