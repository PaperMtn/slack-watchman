## 3.0.1 - 2020-09-06
### Added
- CHANGELOG to track updates
- MANIFEST.in to ensure required files get packaged for PyPI

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
