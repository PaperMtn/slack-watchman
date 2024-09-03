from dataclasses import dataclass
from typing import List


@dataclass(frozen=True, slots=True)
class TestCases:
    match_cases: List[str]
    fail_cases: List[str]


@dataclass(frozen=True, slots=True)
class Signature:
    """ Class that handles loaded signature objects. Signatures
    define what to search for in Slack and where to search for it.
    They also contain regex patterns to validate data that is found"""

    name: str
    status: bool
    author: str
    date: str
    version: str
    description: str
    severity: int
    watchman_apps: List[str]
    category: str
    scope: List[str]
    file_types: List[str]
    test_cases: TestCases
    search_strings: str
    patterns: List[str]
