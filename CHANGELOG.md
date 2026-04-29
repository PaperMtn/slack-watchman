# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- **[High]** Message and file workers now cache `users.info` and `conversations.info` lookups by ID for the lifetime of the worker. Previously every match triggered fresh API calls, so a worker with 1000 matches that referenced 5 unique users + 3 unique channels made 2000 API round trips; it now makes 8. Caches are per-worker (no cross-worker IPC), and the file worker preserves its existing defensive `is_dataclass` check via a small `_resolve_file_user` helper. Fixes [#117](https://github.com/PaperMtn/slack-watchman/issues/117)
- **[High]** `find_messages` and `find_files` now run their per-query workers through a bounded `multiprocessing.Pool` instead of starting one `multiprocessing.Process` per search string. The pool is capped at `_DEFAULT_POOL_SIZE` (8), so a signature with N search strings spawns `min(8, N)` workers regardless of how long the list is — memory and file-descriptor usage no longer scale with signature size and the Slack API isn't hit with as many simultaneous requests. Fixes [#113](https://github.com/PaperMtn/slack-watchman/issues/113)
- **[High]** Each pool worker now constructs its own `SlackClient` once via a pool initializer (`_init_worker_client`), instead of receiving the parent's pickled client as a task argument. The connection pool / retry config configured on the parent client is therefore reproduced in each worker rather than being silently dropped during pickling. The parent's pre-extracted `session_token` and `cookie_dict` are threaded through, so workers do not redo the cookie -> session-token HTTP roundtrip on startup. Fixes [#114](https://github.com/PaperMtn/slack-watchman/issues/114)
- **[High]** `SlackClient.__init__` now accepts keyword-only `session_token` and `cookie_dict` parameters. Existing token / cookie auth paths are unchanged; the new parameters are used by `_init_worker_client` to rebuild a client in each pool worker without re-running `_get_session_token`.
- **[High]** `find_messages` and `find_files` now share a single `multiprocessing.Manager` per call inside a `with` block, instead of instantiating a separate `Manager()` for each shared list (results, potential matches, errors). One manager subprocess is started per call and shut down deterministically when the block exits, instead of three managers per call leaking until garbage collection / `atexit`. Fixes [#116](https://github.com/PaperMtn/slack-watchman/issues/116)

### Fixed
- **[Critical]** `_multipro_message_worker` and `_multipro_file_worker` now wrap their bodies in `try`/`except` and append failures to a shared `errors` Manager list. Previously, an exception inside a worker (e.g. an exhausted rate-limit retry, malformed search payload, or `AttributeError` on a missing field) would silently kill the child process — `join()` would return cleanly and the parent would lose results for that signature/query with no log output. `find_messages` and `find_files` now log an `ERROR` line per captured failure after `join()`. Fixes [#108](https://github.com/PaperMtn/slack-watchman/issues/108)
- **[Critical]** `_multipro_message_worker` no longer crashes with `AttributeError` when a search result has no `channel` field or the channel id is `None`. The previous `message.get('channel').get('id')` chain failed for DMs, tombstoned messages, and certain bot/system messages; the lookup is now `(message.get('channel') or {}).get('id')`, which falls through to `c = None` instead of taking down the worker. Fixes [#109](https://github.com/PaperMtn/slack-watchman/issues/109)
- **[Critical]** `_multipro_file_worker` no longer crashes with `AttributeError` when a file's `name` or `filetype` is missing or `None`. Slack files in deleted/redacted/tombstoned states can return null values for these fields, and the previous `file_dict.get('name').lower()` / `file_dict.get('filetype').lower()` calls would raise on `None`. Both fields are now coerced via `(file_dict.get(...) or '').lower()` once per file, so non-matching files are skipped instead of taking down the worker. Fixes [#110](https://github.com/PaperMtn/slack-watchman/issues/110)
- **[Critical]** The top-level error handler in `main()` no longer crashes with `AttributeError` when an exception is raised before `init_logger` runs. `OUTPUT_LOGGER` was being initialised to `''` at the top of `main()` and only replaced with a real logger after argparse + the package-metadata lookup; any failure in between (e.g. `metadata.metadata('slack-watchman')`) would fall into `except Exception` and call `''.log(...)`, masking the original error. The placeholder is now `None` and both the `TimeoutError` and `Exception` handlers fall back to `traceback.print_exc()` when the logger has not been initialised yet. Fixes [#111](https://github.com/PaperMtn/slack-watchman/issues/111)
- **[High]** `SlackClient._make_request` now honours the `Retry-After` header on 429 responses (falling back to a 90s default) instead of always sleeping for a fixed 90 seconds. The retry now loops back through `_make_request` so consecutive 429s receive the same handling rather than the second one propagating as a raw `HTTPError`; retries are capped (default 5) and exhaustion raises an informative `HTTPError` rather than spinning forever. Fixes [#115](https://github.com/PaperMtn/slack-watchman/issues/115)
- **[Medium]** `find_auth_information`'s return-type annotation has been widened from `Dict[str, List[str]] | None` to `Dict[str, Any] | None`. The actual payload mixes lists, booleans, strings and `None` (from the workspace login page's `data-props` blob), so the previous annotation was never accurate; type checkers and any caller trusting it (e.g. trying to iterate every value as a list) would have been wrong. Fixes [#124](https://github.com/PaperMtn/slack-watchman/issues/124)
- **[Medium]** `find_auth_information` now catches `requests.RequestException`, `json.JSONDecodeError`, and `AttributeError` instead of letting them propagate. The function does an unauthenticated scrape of the workspace login page after authenticated auth has already succeeded, so a transient network blip or a Slack-side HTML/`data-props` schema change previously aborted the entire scan. Failures now return `None` (matching the existing "no info available" contract) and emit a `WARNING` via an optional `logger` argument; both call sites in `__init__.py` pass `OUTPUT_LOGGER`. Fixes [#123](https://github.com/PaperMtn/slack-watchman/issues/123)
- **[Medium]** `find_messages` and `find_files` now explicitly return `[]` on the no-match and exception paths instead of falling through with an implicit `None`. Both functions are annotated `-> List[Dict]`, so callers iterating or measuring the result without a truthy guard would have crashed; existing callers are unaffected because they happened to use `if results:`. Fixes [#118](https://github.com/PaperMtn/slack-watchman/issues/118)
- **[Medium]** `_multipro_file_worker` no longer appends a duplicate `results_dict` for each `sig.file_types` entry that substring-matches a file's `filetype`. The per-file_type loop has been replaced with a single `any(...)` check, so each matching file produces exactly one entry on the shared results list. The post-hoc `watchman_id` dedup pass already collapsed these duplicates, but the were inefficiencies with wasted dataclass construction, `Manager` IPC traffic, and worker-side memory. Fixes [#119](https://github.com/PaperMtn/slack-watchman/issues/119)
- **[Medium]** Removed the dead `dataclasses.is_dataclass` guard from `_resolve_file_user` (and the now-unused `dataclasses` import). `file_dict['user']` only ever holds a raw user-ID string from `search.files`, so the dataclass-instance branch was unreachable. The historical asymmetry between the file_types and no-file_types branches in `_multipro_file_worker` had already been resolved when both branches were unified through `_resolve_file_user` during the caching refactor; this drops the leftover defensive check. Fixes [#120](https://github.com/PaperMtn/slack-watchman/issues/120)
- **[Medium]** `_multipro_message_worker` now skips messages with no text instead of coercing `None` into the literal string `'None'` and feeding it to the signature regex. The previous `str(message.get('text'))` call meant a permissive pattern (e.g. one that matched `None`) could false-positive on attachment-only messages, certain bot/system events, and any other shape Slack returns without a `text` field. Empty/missing text is now an explicit `continue`. Fixes [#122](https://github.com/PaperMtn/slack-watchman/issues/122)
- **[Medium]** `_multipro_message_worker` now compiles each `sig.patterns` entry once per worker invocation and reuses the resulting `Match` object instead of recompiling per message and calling `Pattern.search` a second time to extract `.group(0)`. A worker processing N messages against P patterns previously did `N * P` compiles and up to `2 * N * P` searches; it now does P and `N * P`. CPython's internal regex cache was masking some of the cost, but the duplicate `search` call on the matching path was real work. Fixes [#121](https://github.com/PaperMtn/slack-watchman/issues/121)

## [4.5.0] - 2026-04-28
### Fixed
- Canvas results in `StdoutLogger` were rendered with the red `USER` colour scheme because `msg_level` was set to `'USER'` instead of `'CANVAS'`. Added a dedicated `CANVAS` style branch in `log_to_stdout`. Fixes [#90](https://github.com/PaperMtn/slack-watchman/issues/90)
- Fixed `AttributeError` crash in `StdoutLogger` when logging file results with no resolved user. The user dict is now coerced via `(message.get('user') or {})` before reading `display_name`/`email`. Fixes [#91](https://github.com/PaperMtn/slack-watchman/issues/91)
- Removed pointless retry on `log_to_stdout` exception in `StdoutLogger.log`. The previous handler retried with identical arguments and could only fail the same way; replaced with a single contextual error message. Fixes [#92](https://github.com/PaperMtn/slack-watchman/issues/92) (thanks @SAY-5)
- A formatting failure inside `StdoutLogger.log_to_stdout` no longer terminates the process when debug mode is enabled. The `sys.exit(1)` call has been removed; the traceback is still printed in debug mode and the scan continues. Fixes [#95](https://github.com/PaperMtn/slack-watchman/issues/95)
- `JSONLogger` no longer subclasses `logging.Logger` (the inheritance was unused — every emission already went through `self.logger`) and no longer stacks duplicate handlers when instantiated more than once. `addHandler` is now guarded so the process-wide singleton from `logging.getLogger('Slack Watchman')` keeps a single handler. Fixes [#98](https://github.com/PaperMtn/slack-watchman/issues/98)
- `JSONLogger.log` now matches `WORKSPACE_PROBE` (the level the caller actually passes) instead of `WORKSPACE_PROBE_INFORMATION`. Probe results were silently falling through to the catch-all `else` branch and being emitted as `CRITICAL` with the wrong formatter. Fixes [#99](https://github.com/PaperMtn/slack-watchman/issues/99)
- `JSONLogger.log` now has explicit `WARNING`, `ERROR`, and `CRITICAL` branches that call the matching `self.logger.warning/error/critical` method. Previously all three (and any unknown level) hit the catch-all `else` and were emitted as `CRITICAL`, so JSON output diverged from `StdoutLogger` and lost severity information. Fixes [#100](https://github.com/PaperMtn/slack-watchman/issues/100)
- `export_csv` now returns a `bool` indicating whether the CSV was written, and its callers in `__init__.py` log a `SUCCESS` only on success and an `ERROR` on failure. Previously a write error was swallowed and the user saw a `Users output to CSV file: ...` success line for a file that was never written. Also corrected the channels CSV success message (it was incorrectly labelled `Users output to CSV file`). Fixes [#102](https://github.com/PaperMtn/slack-watchman/issues/102)
- `export_csv` now guards against empty input. The previous `dataclasses.asdict(export_data[0])` would raise `IndexError`, which was hidden by the bare `except` and reported only as a stray `print` line. Empty input now returns `False` without opening a file. Fixes [#103](https://github.com/PaperMtn/slack-watchman/issues/103)

### Removed
- Redundant `f.close()` call in `export_csv` after the `with open(...) as f:` block (the context manager already closes the file). Fixes [#104](https://github.com/PaperMtn/slack-watchman/issues/104)

### Changed
- Converted the `notify_type` cascade in `StdoutLogger.log` from a series of independent `if`s to an `elif` chain, since the branches are mutually exclusive. Avoids unnecessary string comparisons on every log call. Fixes [#94](https://github.com/PaperMtn/slack-watchman/issues/94)
- Hoisted the colourising regexes (`_TYPE_COLORER`, `_HEADER_WORDS`) in `loggers.py` to module-level constants instead of recompiling them on every `log_to_stdout` call. Fixes [#96](https://github.com/PaperMtn/slack-watchman/issues/96)
- Replaced the 13 near-identical `elif` colour branches in `StdoutLogger.log_to_stdout` with a `_LEVEL_STYLES` dict lookup. Behaviour is unchanged for every existing level. Fixes [#97](https://github.com/PaperMtn/slack-watchman/issues/97)
- Replaced the per-call `handler.setFormatter` mutation in `JSONLogger.log` with a single `_JSONFormatter` that builds the JSON envelope from `record.msg` and an `extra`-supplied `log_level`. Eliminates the eight `*_format` attributes, removes the not-thread-safe handler state swap, and keeps the JSON schema unchanged for every existing level. Fixes [#101](https://github.com/PaperMtn/slack-watchman/issues/101)

## [4.4.5] - 2026-04-27
### Changed
- Updated dependabot.yml to created PRs against `develop` branch instead of `maaster`
- Dependabot updates:
  - `requests` updated to `2.33.1`
  - `pygments` updated to `2.20.0`
  - `pytest` updated to `9.0.3`

## [4.4.4] - 2026-03-29
### Added
- Added GitHub Action to test release notes and version tag for GitHub releases

### Changed
- Dependabot updates
  - `requests` updated to `2.33.0`
- Update GitHub Actions that use Node.js 20 to the latest versions to support Node.js 24

### Fixed
- Fixed broken link to Slack Cookie Authentication blog post in README (raised in [#82] by @emilstahl)

## [4.4.3] - 2025-12-06
### Changed
- Dependabot updates
  - `urllib3` updated to `2.6.0`

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
