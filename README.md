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
Slack Watchman looks for:

<<<<<<< HEAD
- Tokens
  - AWS keys
  - GCP keys
  - Azure keys
  - Google API keys
  - Slack API keys & webhooks
  - Twitter API keys
      - Access token
      - oauth_token
      - oauth_token_secret
  - Facebook API Keys
      - Access token
      - Secret keys
  - GitHub keys
  - Private keys
  - Bearer tokens
=======
- API Keys, Tokens & Service Accounts
  - AWS, Azure, GCP, Google API, Slack (keys & webhooks), Twitter, Facebook, GitHub
  - Generic Private keys
  - Access Tokens, Bearer Tokens, Client Secrets, Private Tokens
>>>>>>> release/3.0.0
- Files
    - Certificate files
    - Potentially interesting/malicious/sensitive files (.docm, .xlsm, .zip etc.)
    - Executable files
    - Keychain files
    - Config files for popular services (Terraform, Jenkins, OpenVPN and more)
- Personal Data
    - Leaked passwords
    - Passport numbers, Dates of birth, Social security numbers, National insurance numbers, Drivers licence numbers (UK), Individual Taxpayer Identification Number
- Financial data
    - Paypal Braintree tokens, Bank card details, IBAN numbers, CUSIP numbers

It also gives the following, which can be used for general auditing:
- User data
    - All users & all admins
- Channel data
    - All channels, including externally shared channels

#### Time based searching
You can run Slack Watchman to look for results going back as far as:
- 24 hours
- 7 days
- 30 days
- All time

This means after one deep scan, you can schedule Slack Watchman to run regularly and only return results from your chosen timeframe.

### Rules
Slack Watchman uses custom YAML rules to detect matches in Slack.

They follow this format:

```
---
filename:
enabled: [true|false]
meta:
  name:
  author:
  date:
  description: *what the search should find*
  severity: *rating out of 100*
category: [files|tokens|financial|pii]
scope:
- [files|messages]
file_types: *optional list for use with file searching*
test_cases:
  match_cases:
  - *test case that should match the regex*
  fail_cases:
  - *test case that should not match the regex*
strings:
- *search query to use in Slack*
pattern: *Regex pattern to filter out false positives*
```
There are Python tests to ensure rules are formatted properly and that the Regex patterns work in the `tests` dir

More information about rules, and how you can add your own, is in the file `docs/rules.md`.

### Logging

Slack Watchman gives the following logging options:
- CSV
- Log file
- Stdout
- TCP stream

When using CSV logging, searches for rules are returned in separate CSV files, for all other methods of logging, results are output in JSON format, perfect for ingesting into a SIEM or other log analysis platform.

For file and TCP stream logging, configuration options need to be passed via `.conf` file or environment variable. See the file `docs/logging.md` for instructions on how to set it up.

If no logging option is given, Slack Watchman defaults to CSV logging.

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
Configuration options can be passed in a file named `watchman.conf` which must be stored in your home directory. The file should follow the YAML format, and should look like below:
```
slack_watchman:
  token: xoxp-xxxxxxxx
  logging:
    file_logging:
      path:
    json_tcp:
      host:
      port:
```
Slack Watchman will look for this file at runtime, and use the configuration options from here. If you are not using the advanced logging features, leave them blank.

If you are having issues with your .conf file, run it through a YAML linter.

An example file is in `docs/example.conf`

## Installation
Install via pip

`pip install slack-watchman`

## Usage
Slack Watchman will be installed as a global command, use as follows:
```
usage: slack-watchman [-h] --timeframe {d,w,m,a}
                      [--output {csv,file,stdout,stream}] [--version] [--all]
                      [--users] [--channels] [--pii] [--financial] [--tokens]
                      [--files] [--custom CUSTOM]

Monitoring your Slack workspaces for sensitive information

optional arguments:
  -h, --help            show this help message and exit
  --output {csv,file,stdout,stream}
                        Where to send results
  --version             show program's version number and exit
  --all                 Find everything
  --users               Find all users
  --channels            Find all channels
  --pii                 Find personal data: Passwords, DOB, passport details,
                        drivers licence, ITIN, SSN
  --financial           Find financial data: Card details, PayPal Braintree
                        tokens, IBAN numbers, CUSIP numbers
  --tokens              Find tokens: Private keys, AWS, GCP, Google API,
                        Slack, Slack webhooks, Facebook, Twitter, GitHub
  --files               Find files: Certificates, interesting/malicious files
  --custom              Search for user defined custom search queries that you
                        have created rules for

required arguments:
  --timeframe {d,w,m,a}
                        How far back to search: d = 24 hours w = 7 days, m =
                        30 days, a = all time
  ```

You can run Slack Watchman to look for everything, and output to default CSV:

`slack-watchman --timeframe a --all`

Or arguments can be grouped together to search more granularly. This will look for tokens and files for the last 30 days, and output the results to a TCP stream:

`slack-watchman --timeframe m --tokens --files --output stream`
