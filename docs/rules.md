# Rules
Slack Watchman uses rules to provide the search terms to query Slack and Regex patterns to filter out true positives.

They are written in YAML, and follow this format:
```yaml
---
filename:
enabled: [true|false]
meta:
  name:
  author:
  date:
  description: #what the search should find
  severity: #rating out of 100
category: #[files|tokens|financial|pii]
scope:
- #[files|messages]
file_types: #optional list for use with file searching
test_cases:
  match_cases:
  - #test case that should match the regex*
  fail_cases:
  - #test case that should not match the regex*
strings:
- #search query to use in Slack*
pattern: #Regex pattern to filter out false positives*
```

Rules are stored in the directory watchman/rules, so you can see examples there.

**Category**
The category the rule comes under, to be used with granular searching command line options. Includes custom, which used to be fed in by a txt file

**Scope**
This is what Slack should look for: messages or files. You can also use both, with each on its own line

**File Type**
This is an optional field. Can be used to search for files and only match certain types. E.g. looking for the search term `CV` in the name of files of the type `docx`

[This page from Slack](https://api.slack.com/types/file) details the available filetypes.

If you are not searching files, or aren't bothered about file type, leave this blank.

**Test cases**
These test cases are used to check that the regex pattern works. Each rule should have at least one match (pass) and one fail case.

If you want to return all results found by a query, enter the value `blank` for both cases. For example, when you are searching for all files. (See `word_files.yaml` for an example)

## Creating your own rules
You can easily create your own rules for Slack Watchman. The two most important parts are the search queries and the regex pattern.

### Search queries
These are stored as the entries in the 'strings' section of the rule, and are the search terms used to query Slack to find results.

Multiple entries can be put under strings to find as many potential hits as you can. So if I wanted to find social security numbers, I might use both of these search terms:
`- ssn`
`- social security`


#### Search terminology
The Slack API follows the same rules for searching as the web client, meaning you can use the same modifiers and filters in your search queries.

[This Slack help article](https://slack.com/intl/en-gb/help/articles/202528808-Search-in-Slack#desktop-2) gives information on what modifiers and advanced search features are available.

The most important modifier is the use of quotation marks to search for literal strings. The search term `".doc"` will search for the exact string `.doc`. Searching without quotation marks would find any string containing close matches to `.doc`, so it would pick up the string `doctor`

For this reason, it is recommend when searching for files to put the file extension in quotes: `".zip"`

### Regex pattern
This pattern is used to filter results that are returned by the search query.

If you want to return all results found by a query, enter the value `''` for the pattern. For example, when you are searching for all files. (See `word_files.yaml` for an example)
