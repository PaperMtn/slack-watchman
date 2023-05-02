import pathlib
import yaml
from dataclasses import dataclass
from typing import List


@dataclass(slots=True)
class TestCases:
    match_cases: List[str]
    fail_cases: List[str]


@dataclass(slots=True)
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


def load_from_yaml(sig_path: pathlib.PosixPath) -> List[Signature]:
    """Load YAML file and return a Signature object
    Args:
        sig_path: Path of YAML file
    Returns:
        Signature object with fields populated from the YAML
        signature file
    """

    with open(sig_path) as yaml_file:
        yaml_import = yaml.safe_load(yaml_file)

        output = []
        for sig in yaml_import.get('signatures'):
            if 'slack_std' in sig.get('watchman_apps'):
                output.append(Signature(
                    name=sig.get('name'),
                    status=sig.get('status'),
                    author=sig.get('author'),
                    date=sig.get('date'),
                    version=sig.get('version'),
                    description=sig.get('description'),
                    severity=sig.get('severity'),
                    watchman_apps=sig.get('watchman_apps'),
                    category=sig.get('watchman_apps').get('slack_std').get('category'),
                    scope=sig.get('watchman_apps').get('slack_std').get('scope'),
                    file_types=sig.get('watchman_apps').get('slack_std').get('file_types'),
                    test_cases=TestCases(
                        match_cases=sig.get('test_cases').get('match_cases'),
                        fail_cases=sig.get('test_cases').get('fail_cases')
                    ),
                    search_strings=sig.get('watchman_apps').get('slack_std').get('search_strings'),
                    patterns=sig.get('patterns')))

    return output
