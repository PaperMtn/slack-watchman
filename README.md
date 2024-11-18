<img src="https://i.imgur.com/jeU9F0a.png" width="550">

# Slack Watchman
![Python 2.7 and 3 compatible](https://img.shields.io/pypi/pyversions/slack-watchman)
![PyPI version](https://img.shields.io/pypi/v/slack-watchman.svg)
![License: MIT](https://img.shields.io/pypi/l/slack-watchman.svg)

Monitoring and enumerating Slack for exposed secrets

## About Slack Watchman
<img src="/images/slack_watchman.png" width="500">

Slack Watchman is an application that uses the Slack API to find potentially sensitive data exposed in a Slack workspace, and to enumerate other useful information for red, blue and purple teams.

More information about Slack Watchman can be found [on my blog](https://papermtn.co.uk/slack-watchman-monitoring-slack-workspaces-for-sensitive-information/).

### Features
#### Secrets Detection
<img src="/images/slack_watchman_finding.png" width="500">

Slack Watchman looks for:

- API Keys, Tokens & Service Accounts
  - AWS, Azure, GCP, Google API, Slack (keys & webhooks), Twitter, Facebook, GitHub and more
  - Generic Private keys
  - Access Tokens, Bearer Tokens, Client Secrets, Private Tokens
- Files
    - Certificate files
    - Potentially interesting/malicious/sensitive files (.docm, .xlsm, .zip etc.)
    - Executable files
    - Keychain files
    - Config files for popular services (Terraform, Jenkins, OpenVPN and more)
- Personal Data
    - Leaked passwords
    - Passport numbers, Dates of birth, Social security numbers, National insurance numbers and more
- Financial data
    - Paypal Braintree tokens, Bank card details, IBAN numbers, CUSIP numbers and more

#### Time based searching
You can run Slack Watchman to look for results going back as far as:
- 24 hours
- 7 days
- 30 days
- All time

#### Enumeration
<img src="/images/slack_watchman_enumeration.png" width="500">

It also enumerates the following:
- User data
    - All users & all admins
- Conversation data
    - All conversations, including externally shared conversations
    - All conversations that include a Slack Canvas (which often contain sensitive or important information)
- Workspace authentication options


This means after one deep scan, you can schedule Slack Watchman to run regularly and only return results from your chosen timeframe.

#### Unauthenticated Probe
<img src="/images/slack_watchman_probe.png" width="500">

You can run Slack Watchman in unauthenticated probe mode to enumerate authentication options and other information on a Workspace. This doesn't need a token, and returns:

- Workspace name
- Workspace ID
- Approved domains (which can create accounts)
- OAuth providers
- SSO auth status
- Two-factor requirements

To run this mode use Slack Watchman with the `--probe` flag and the workspace domain to probe:

```commandline
slack-watchman --probe https://domain.slack.com
```

### Signatures
Slack Watchman uses custom YAML signatures to detect matches in Slack. These signatures are pulled from the central [Watchman Signatures repository](https://github.com/PaperMtn/watchman-signatures). Slack Watchman automatically updates its signature base at runtime to ensure its using the latest signatures to detect secrets.

#### Suppressing Signatures
You can define signatures that you want to disable when running Slack Watchman by adding their IDs to the `disabled_signatures` section of the `watchman.conf` file. For example:

```yaml
slack_watchman:
  token: ...
  cookie: ...
  url: ...
  disabled_signatures:
    - tokens_generic_bearer_tokens
    - tokens_generic_access_tokens
```

You can find the ID of a signature in the individual YAML files in [Watchman Signatures repository](https://github.com/PaperMtn/watchman-signatures).

### Logging

Slack Watchman gives the following logging options:
- Terminal-friendly Stdout
- JSON to Stdout

Slack Watchman defaults to terminal-friendly stdout logging if no option is given. This is designed to be easier for humans to read.

JSON logging is also available, which is perfect for ingesting into a SIEM or other log analysis platforms.

JSON formatted logging can be easily redirected to a file as below:
```commandline
slack-watchman --timeframe a --all --output json >> slack_watchman_log.json 
```

## Authentication Requirements
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
**Note**: User tokens act on behalf of the user who authorises them, so I would suggest you create this app and authorise it using a service account, otherwise the app will have access to your private conversations and chats.

### Cookie Authentication
Alternatively, Slack Watchman can also authenticate to Slack using a user `d` cookie, which is stored in the browser of each user logged into a workspace.

To use cookie authentication, you will need to provide the `d` cookie, and the URL of the target workspace. Then you will need to use the `--cookie` flag when running Slack Watchman

More information on cookie authentication can be found [on my blog](https://papermtn.co.uk/category/tools/slack-watchman/)
#### Providing tokens
Slack Watchman will first try to get the Slack token (plus the cookie token and URL if selected) from the environment variables 
- `SLACK_WATCHMAN_TOKEN`
- `SLACK_WATCHMAN_COOKIE`
- `SLACK_WATCHMAN_URL`

If this fails it will try to load the token(s) from `.conf` file (see below).

#### watchman.conf file
Configuration options can be passed in a file named `watchman.conf` which must be stored in your home directory. The file should follow the YAML format, and should look like below:
```yaml
slack_watchman:
  token: xoxp-xxxxxxxx
  cookie: xoxd-%2xxxxx
  url: https://xxxxx.slack.com
  disabled_signatures:
    - tokens_generic_bearer_tokens
    - tokens_generic_access_tokens
```
Slack Watchman will look for this file at runtime, and use the configuration options from here. If you are not using cookie auth, leave `cookie` and `url` blank.

If you are having issues with your .conf file, run it through a YAML linter.

An example file is in `docs/example.conf`

**Note**: Cookie and URL values are optional, and not required if not using cookie authentication.

## Installation
You can install the latest stable version via pip:

```commandline
python3 -m pip install slack-watchman
```

Or build from source yourself:

Download the release source files, then from the top level repository run:
```commandline
python3 -m pip build
python3 -m pip install --force-reinstall dist/*.whl
```

## Docker Image

Slack Watchman is also available from the Docker hub as a Docker image:

`docker pull papermountain/slack-watchman:latest`

You can then run Slack Watchman in a container, making sure you pass the required environment variables:

```commandline
// help
docker run --rm papermountain/slack-watchman -h

// scan all
docker run --rm -e SLACK_WATCHMAN_TOKEN=xoxp... papermountain/slack-watchman --timeframe a --all --output json
docker run --rm --env-file .env papermountain/slack-watchman --timeframe a --all --output stdout
```

## Usage
Slack Watchman will be installed as a global command, use as follows:
```commandline
usage: slack-watchman [-h] [--timeframe {d,w,m,a}] [--output {json,stdout}] [--version] [--all] [--users] [--channels] [--pii] [--secrets] [--debug] [--verbose] [--cookie] [--probe PROBE_DOMAIN]

Monitoring and enumerating Slack for exposed secrets

options:
  -h, --help            show this help message and exit
  --timeframe {d,w,m,a}, -t {d,w,m,a}
                        How far back to search: d = 24 hours w = 7 days, m = 30 days, a = all time
  --output {json,stdout}, -o {json,stdout}
                        Where to send results
  --version, -v         show program's version number and exit
  --all, -a             Find secrets and PII
  --users, -u           Enumerate users and output them to .csv in the current working directory
  --channels, -c        Enumerate channels and output them to .csv in the current working directory
  --pii, -p             Find personal data: DOB, passport details, drivers licence, ITIN, SSN etc.
  --secrets, -s         Find exposed secrets: credentials, tokens etc.
  --debug, -d           Turn on debug level logging
  --verbose, -V         Turn on more verbose output for JSON logging. This includes more fields, but is larger
  --cookie              Use cookie auth using Slack d cookie. REQUIRES either SLACK_WATCHMAN_COOKIE and SLACK_WATCHMAN_URL environment variables set, or both values set in watchman.conf
  --probe PROBE_DOMAIN  Perform an un-authenticated probe on a workspace for available authentication options and other information. Enter workspace domain to probe
  ```

You can run Slack Watchman to look for everything, and output to default stdout:

```commandline
slack-watchman --timeframe a --all
```

## Other Watchman apps
You may be interested in the other apps in the Watchman family:
- [Slack Watchman for Enterprise Grid](https://github.com/PaperMtn/slack-watchman-enterprise-grid)
- [GitLab Watchman](https://github.com/PaperMtn/gitlab-watchman)
- [GitHub Watchman](https://github.com/PaperMtn/github-watchman)

## License
The source code for this project is released under the [GNU General Public Licence](https://www.gnu.org/licenses/licenses.html#GPL). This project is not associated with Slack Technologies or Salesforce.