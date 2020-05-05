![Slack Watchman](files/Slack_watchman_alt_var_1280x320.png)

# Slack Watchman
![Python 2.7 and 3 compatible](https://img.shields.io/badge/python-2.7%2C%203.x-blue.svg)
![PyPI version](https://img.shields.io/pypi/v/lil-pwny.svg)
![License: MIT](https://img.shields.io/pypi/l/lil-pwny.svg)

Monitoring you Slack workspaces for sensitive information

## About Slack Watchman
Slack Watchman is an application that uses the Slack API to look for potentially sensitive data exposed in your Slack workspaces.

### Features
Slack Watchman searches for, and reports back on:

- Externally shared channels
- Potential leaked passwords
- AWS Keys
- GCP keys
- Slack API keys
- Private keys
- Bank card details
- Certificate files
- Potentially interesting/malicious files (.docm, .xlsm, .zip etc.)

It also gives the following, which can be used for general auditing:
- All channels
- All users
- All admins

#### Time based searching
You can run Slack Watchman to look for results going back as far as:
- 7 days
- 30 days
- All time

This means after one deep scan, you can schedule Slack Watchman to run regularly and only return results from your chosen timeframe.

## Installation
Install via pip

`pip install slack-watchman`

## Usage
Slack Watchman will be installed as a global command, use as follows:
```
usage: slack-watchman [-h] --timeframe {w,m,a} [--all] [-U] [-C] [-a] [-g] [-s]
                   [-p] [-c] [-t] [-f] [-P]

Slack Watchman: Monitoring you Slack workspaces for sensitive information

optional arguments:
  -h, --help           show this help message and exit
  --timeframe {w,m,a}  How far back to search: w = one week, m = one month, a
                       = all time
  --all                Find everything
  -U, --users          Find all users, including admins
  -C, --channels       Find all channels, including external shared channels
  -a                   Look for AWS keys
  -g                   Look for GCP keys
  -s                   Look for Slack tokens
  -p                   Look for private keys
  -c                   Look for card details
  -t                   Look for certificate files
  -f                   Look for interesting files
  -P                   Look for passwords
  ```

You can run Slack Watchman to look for everything:
`slack-watchman --timeframe a --all`

Or arguments can be grouped together to search more granularly. This will look for AWS keys, GCP keys and passwords for the last 30 days:
`slack-watchman --timeframe m -agP`


## TODO
- a more elegant solution for managing config files
