<img src="https://i.imgur.com/RsZPaC9.png" width="550">

# Slack Watchman
![Python 2.7 and 3 compatible](https://img.shields.io/pypi/pyversions/slack-watchman)
![PyPI version](https://img.shields.io/pypi/v/slack-watchman.svg)
![License: MIT](https://img.shields.io/pypi/l/slack-watchman.svg)

Monitoring your Slack workspaces for sensitive information

## About Slack Watchman
Slack Watchman is an application that uses the Slack API to look for potentially sensitive data exposed in your Slack workspaces.

More information about Slack Watchman can be found [on my blog](https://papermtn.co.uk/slack-watchman-monitoring-slack-workspaces-for-sensitive-information/).

### Features
Slack Watchman searches for, and reports back on:

- Externally shared channels
- Potential leaked passwords
- AWS keys
- GCP keys
- Google API keys
- Slack API keys & webhooks
- Twitter API keys
    - Access token
    - oauth_token
    - oauth_token_secret
- Facebook API Keys
    - Access token
    - Secret keys
- Private keys
- Paypal Braintree tokens
- Bank card details
- Certificate files
- Potentially interesting/malicious files (.docm, .xlsm, .zip etc.)
- Passport numbers
- Dates of birth

It also gives the following, which can be used for general auditing:
- All channels
- All users
- All admins

#### Time based searching
You can run Slack Watchman to look for results going back as far as:
- 24 hours
- 7 days
- 30 days
- All time

This means after one deep scan, you can schedule Slack Watchman to run regularly and only return results from your chosen timeframe.

## Requirements
### Slack API token
To run Slack Watchman, you will need a Slack API OAuth access token. You can do this by creating a simple [Slack App](https://api.slack.com/apps).

The app needs to have the following **User Token Scopes** added:
```
channels:read
files:read
groups:read
im:read
links:read
mpim:read
remote_files:read
search:read
team:read
users:read
users:read.email
```
**Note**: User tokens act on behalf of the user who authorises them, so I would suggest you create this app and authorise it using a service account, otherwise the app will have access to your private channels and chats.

#### Providing token
Slack Watchman will first try to get the the Slack token from the environment variable `SLACK_WATCHMAN_TOKEN`, if this fails it will load the token from .conf file (see below).

### .conf file
This API token needs to be stored in a file named `watchman.conf` which is stored in your home directory. The file should take the following format:
```
[auth]
slack_token = xoxp-xxxxxxxxxx-...
```
Slack Watchman will look for this file at runtime, and notify you if it's not there.

## Installation
Install via pip

`pip install slack-watchman`

## Usage
Slack Watchman will be installed as a global command, use as follows:
```
usage: slack-watchman [-h] --timeframe {d,w,m,a} [--version] [--all] [--users]
                   [--channels] [--pii] [--financial] [--tokens] [--files]

Monitoring your Slack workspaces for sensitive information

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --all                 Find everything
  --users               Find all users, including admins
  --channels            Find all channels, including external shared channels
  --pii                 Find personal data: Passwords, DOB, passport details
  --financial           Find financial data: Card details, PayPal Braintree
                        tokens
  --tokens              Find tokens: Private keys, AWS, GCP, Google API,
                        Slack, Slack webhooks, Facebook, Twitter, GitHub
  --files               Find files: Certificates, interesting/malicious files

required arguments:
  --timeframe {d,w,m,a}
                        How far back to search: d = 24 hours w = 7 days, m =
                        30 days, a = all time
  ```

You can run Slack Watchman to look for everything:

`slack-watchman --timeframe a --all`

Or arguments can be grouped together to search more granularly. This will look for AWS keys, GCP keys and passwords for the last 30 days:

`slack-watchman --timeframe m -agP`
