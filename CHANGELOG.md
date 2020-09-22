## 3.0.6 - 2020-09-22
### Changed
- File searching now includes user who posted file via users.list API method
- Logging field name changes = 'type' -> 'detection_type', 'detection' -> 'detection_data'

## 3.0.5 - 2020-09-18
### Changed
- Updated output to strip quotes from query strings. This should allow better JSON parsing with more log ingestors
- File searching was missing file type output in log data in some occasions, now fixed
  
## 3.0.4 - 2020-09-10
### Added
- Added rules to search for:
  - CV files
  - Files and spreadsheets containing budget and salary information

## 3.0.2 - 2020-09-06
### Added
- CHANGELOG to track updates
- Small bug meant that PyPI installations weren't including the YAML rule files. This has now been fixed.

### Changed
- Top level dir renamed from `watchman` to `slack_watchman` to place nicer with PyPI

## 3.0.0 - 2020-09-04
### Added
- Rules based searching
- Logging options: Log file, Stdout, TCP stream
- Deduplication of output
- Refactor into slack_wrapper to use a class to create an API client

### Changed
- Top level dir renamed from `watchman` to `slack_watchman` to place nicer with PyPI

### Removed
- Custom search by CSV. This is now done by creating your own custom rule
