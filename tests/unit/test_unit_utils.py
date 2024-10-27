from dataclasses import dataclass
from typing import Dict, Any

import pytest

from slack_watchman.utils import (
    convert_timestamp,
    convert_to_dict,
    deduplicate_results
)


def test_convert_timestamp():
    # Test with integer timestamp
    timestamp = 1704067200
    expected_output = "2024-01-01 00:00:00 UTC"
    assert convert_timestamp(timestamp) == expected_output

    # Test with string timestamp
    timestamp = "1704067200.000"
    expected_output = "2024-01-01 00:00:00 UTC"
    assert convert_timestamp(timestamp) == expected_output

    # Test with None input
    timestamp = None
    expected_output = None
    assert convert_timestamp(timestamp) == expected_output


def test_convert_timestamp_edge_cases():
    # Test with very large timestamp
    timestamp = 2 ** 31 - 1
    expected_output = "2038-01-19 03:14:07 UTC"
    assert convert_timestamp(timestamp) == expected_output

    # Test with very small timestamp
    timestamp = 1
    expected_output = "1970-01-01 00:00:01 UTC"
    assert convert_timestamp(timestamp) == expected_output


@dataclass
class TestClass:
    __test__ = False
    name: str
    age: int


@pytest.fixture
def simple_example_result() -> Dict[Any, Any]:
    return {
            "file": {
                "created": "2024-01-01 00:00:00 UTC",
                "editable": False,
                "user": "UABC123"
            },
            "user": {
                "name": "Joe Bloggs",
                "age": 30,
            },
            "watchman_id": "abc123"
    }


@pytest.fixture
def dataclass_example_result_one() -> Dict[Any, Any]:
    return {
            "file": {
                "created": "2024-01-01 00:00:00 UTC",
                "editable": False,
                "user": "UABC123"
            },
            "user": TestClass(name='Joe Bloggs', age=30),
            "watchman_id": "abc123"
    }


@pytest.fixture
def dataclass_example_result_two() -> Dict[Any, Any]:
    return {
        "match_string": "2840631",
        "message": {
            "created": "2024-01-01 00:00:00 UTC",
            "id": "abcdefghijklmnopqrstuvwxyz",
            "permalink": "https://example.com",
            "text": "This is a message",
            "timestamp": "1729257170.452549",
            "type": "message",
            "user": TestClass(name='John Smith', age=30)
        },
        "watchman_id": "abc1234"
    }


def test_convert_to_dict(simple_example_result: Dict[Any, Any],
                         dataclass_example_result_one: Dict[Any, Any]) -> None:
    # Test with simple example
    assert convert_to_dict(simple_example_result) == simple_example_result

    # Test with dataclass example
    assert convert_to_dict(dataclass_example_result_one) == simple_example_result


def test_deduplicate_results(simple_example_result: Dict[Any, Any],
                             dataclass_example_result_one: Dict[Any, Any],
                             dataclass_example_result_two: Dict[Any, Any]) -> None:
    # Test with a single result
    assert deduplicate_results([simple_example_result]) == [simple_example_result]

    # Test with multiple results containing duplicates
    assert deduplicate_results([simple_example_result, simple_example_result]) == [
        simple_example_result]

    # Test with dataclass example
    assert deduplicate_results([dataclass_example_result_one]) == [convert_to_dict(dataclass_example_result_one)]

    # Test with multiple dataclass examples with no duplicates
    assert deduplicate_results([dataclass_example_result_one, dataclass_example_result_two]) == [
        convert_to_dict(dataclass_example_result_two), convert_to_dict(dataclass_example_result_one)]

    # Test with multiple dataclass examples with duplicates
    assert (deduplicate_results([dataclass_example_result_one, dataclass_example_result_one]) ==
            [convert_to_dict(dataclass_example_result_one)])
