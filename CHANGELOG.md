## [unreleased]
- Added notification for an invalid cookie being passed

## [4.0.1] - 2023-05-05
### Changed
- User output in stdout logging now includes display name and email. The accounts for cases where usernames are nonsensical.

## [4.0.0] - 2023-05-03
This major version release brings multiple updates to Slack Watchman in usability, functionality and behind the scenes improvements.

**Note**: While efforts have been made to make sure there is some backwards compatibility, this release may have some breaking changes on previous versions. Make sure to look at the removed secion

### Added
- Support for centralised signatures from the [Watchman Signatures repository](https://github.com/PaperMtn/watchman-signatures)
  - This makes it much easier to keep the signature base for all Watchman applications up to date, and to add functionality to Slack Watchman with new signatures. New signatures are downloaded, and updates to existing signatures are applied, at runtime, meaning Slack Watchman will always be using the most up to date signatures.
- Major UI overhaul
  - A lot of feedback said Slack Watchman was hard to read. This version introduces new terminal optimised logging as a logging option, as well as JSON formatting. This formatting is now the default when running with no output option selected, and is a lot easier for humans to read. Also, colours!
- Cookie login
  - If you have a Slack `d` cookie (which can be gathered from a web browser authenticated to Slack), and you know the URL of the target Slack workspace, Slack Watchman now allows you to authenticate using cookie auth, instead of supplying a bot token.
- Multiprocessing and other backend improvements
  - Slack Watchman now makes more efficient use of API calls, and incorporates multiprocessing, to run faster than previous versions. Larger workspaces can now be enumerated much quicker.  
- Docker image support
  - Slack Watchman is now available as a Docker image. Simply pull from Docker Hub `docker pull papermountain/slack-watchman:latest`
- More useful enumeration options added
  - Slack Watchman now gathers more information on a workspace. Useful if your use case is more red than blue...
    - Get information on calling user
      - Provides you information on the user you are authenticated as, including whether the user has 2FA configured, whether they are an admin etc.
      - CSV files containing information on all users and channels in the workspace.
- Option choose between verbose or succinct logging when using JSON output. Default is succinct.
- Debug logging option
### Removed
- Socket logging functionality
  - I'm not sure this functionality was used, but the move to more accessible stdout and JSON logging options means that the option to log to a listening socket has been removed.
- Some CSV output
  - For the same reason as above, logging results to CSV has been removed. Enumerating users and channels can still be output to CSV, but formatting a CSV file for a complex nested datastructure is a nightmare, and makes future modifications time consuming.
- Logging to file
  - To keep logging as simple as possible, the file output option has also been removed. This can easily be reproduced by piping the output of running Slack Watchman to a file:
    - ```slack-watchman --timeframe w --all --output json >> sw-log.json```
- Local/custom signatures - Centralised signatures mean that user-created custom signatures can't be used with Slack Watchman for Enterprise Grid anymore. If you have made a signature you think would be good for sharing with the community, feel free to add it to the Watchman Signatures repository, so it can be used in all Watchman applications

## [3.0.10] - 2020-11-08
### Fixed
- Retry added for occasional Requests HTTPSConnectionPool error
### Added
- Version added to Stdout logging
- Better exception handling and logging exceptions correctly
- Workspace field added to critical error

## [3.0.9] - 2020-10-31
### Added
- Mailgun API token rule
- Mailchimp API token rule
- Twilio API token rule
- Stripe API token rule
- Heroku API token rule
- Shodan API token rule
- Cloudflare API token rule

## [3.0.8] - 2020-10-10
### Added
- Exact regex string match added to output from message searches
- Check added for when the given token doesn't have the required API scope. On incorrect scope, and exception will be raised and the required scope will be output to log

## [3.0.7] - 2020-10-02
### Added
- Rule to detect MasterCard Datacash credentials

## [3.0.6] - 2020-09-22
### Changed
- File searching now includes user who posted file via users.list API method
- Logging field name changes = 'type' -> 'detection_type', 'detection' -> 'detection_data'

## [3.0.5] - 2020-09-18
### Changed
- Updated output to strip quotes from query strings. This should allow better JSON parsing with more log ingestors
- File searching was missing file type output in log data in some occasions, now fixed

## [3.0.4] - 2020-09-10
### Added
- Added rules to search for:
  - CV files
  - Files and spreadsheets containing budget and salary information

## [3.0.2] - 2020-09-06
### Added
- CHANGELOG to track updates
- Small bug meant that PyPI installations weren't including the YAML rule files. This has now been fixed.

### Changed
- Top level dir renamed from `watchman` to `slack_watchman` to place nicer with PyPI

## [3.0.0] - 2020-09-04
### Added
- Rules based searching
- Logging options: Log file, Stdout, TCP stream
- Deduplication of output
- Refactor into slack_wrapper to use a class to create an API client

### Changed
- Top level dir renamed from `watchman` to `slack_watchman` to place nicer with PyPI

### Removed
- Custom search by CSV. This is now done by creating your own custom rule
