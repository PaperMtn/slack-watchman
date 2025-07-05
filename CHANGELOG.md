## [4.4.2] - 2025-07-05
### Added
- Added `.github/dependabot.yml` with configuration for Dependabot:
  - Use `develop` as target branch
  - Update both `pyproject.toml` and `poetry.lock`
- README updated to recommend using `pipx` for installation

### Fixed
- Fixed issue with Poetry build arguments in Dockerfile, which was causing the build to fail.

### Changed
- Modified signature download process to use `requests` instead of `urllib`, which is more robust and provides better SSL handling. This addresses the issue raised in [#74](https://github.com/PaperMtn/slack-watchman/issues/74)
- Dependabot updates
  - `urllib3` updated to `2.5.0`
  - `requests` updated to `2.32.4`

## [4.4.1] - 2024-12-18
### Fixed
- Fixed a bug where an exception was raised when no suppressed signatures were passed. Fixes [#66](https://github.com/PaperMtn/slack-watchman/issues/66)
- Fixed error when creating a Workspace object using the response from the Slack API. Validation was expecting a `bool`, but in some instances, a string was being returned. Fixes [#68](https://github.com/PaperMtn/slack-watchman/issues/68)
- Fixed bug where the incorrect error message was being passed when environment variables were not set. Fixes [#67](https://github.com/PaperMtn/slack-watchman/issues/67)

## [4.4.0] - 2024-11-20
### Added
- Ability to disable signatures by their ID in the `watchman.conf` config file.
  - These signatures will not be used when running Slack Watchman
  - Signature IDs for each signature can be found in the [Watchman Signatures repository](https://github.com/PaperMtn/watchman-signatures)
- App manifest JSON file for creating the Slack Watchman Slack application added in `docs/app_manifest.json`
- Pylint configuration and implement fixes and recommendations based on findings
  - Added Pylint checks in GitHub actions
- Additional tests added:
  - Unit tests for remaining non-model modules
  - Integration tests for slack_client.py

### Fixed
- Bug where variables were not being imported from watchman.conf config file

## [4.3.0] - 2024-10-27
### Changed
- Timestamps are now in UTC across all logging for consistency
- Refactor some commonly used functions into a utils module
- More general code cleanup and refactoring

### Fixed
- Fixed a few bugs with models for User, Workspace and Messages not picking up all values

### Added
- GitHub actions for Python tests and Docker build and run testing
- Implemented unit tests for models

## [4.2.0] - 2024-09-27
### Added
- Added enumeration of conversations with populated Canvases attached. These can contain sensitive information, and are worth reviewing.
- Added join domain to unauthenticated probe. This is the link to use to sign into a Workspace if you have an email with one of the approved domains.

## [4.1.2] - 2024-09-14
### Added
- Added enumeration of authentication options for the Workspace you authed to.
  - Shows which domains are authorised to create accounts on the workspace. If a historic domain that isn't registered anymore is still approved, you could access this workspace using an email from it.
  - Also shows which OAuth providers are authorised for the workspace.
- Added new 'unauthenticated probe' mode. This mode will attempt an unauthenticated probe on the workspace and return any available authentication information, as well as any other useful information such as whether the workspace is on a paid plan.
  - No authentication token is required in this mode, you can spray away to any workspace you like.

### Changed
- Signatures are now downloaded, processes and stored in memory instead of writing to disk. This saves having to store them in files, and solves the issues when using Slack Watchman with read-only filesystems (raised in [#51](https://github.com/PaperMtn/watchman-signatures/issues/51)) 
- Migrated to Poetry for dependency control and packaging


## [4.0.2] - 2023-06-14
### Added
- Added notification for an invalid cookie being passed (Fixes [#47](https://github.com/PaperMtn/watchman-signatures/issues/47))
### Fixed
- JSON output for User and Workspace information was malformed, this has now been fixed

## [4.0.1] - 2023-05-05
### Changed
- User output in stdout logging now includes display name and email. The accounts for cases where usernames are nonsensical.

## [4.0.0] - 2023-05-03
This major version release brings multiple updates to Slack Watchman in usability, functionality and behind the scenes improvements.

**Note**: While efforts have been made to make sure there is some backwards compatibility, this release may have some breaking changes on previous versions. Make sure to look at the removed section

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
