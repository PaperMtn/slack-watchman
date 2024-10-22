import time
import json
import dataclasses
from typing import List, Dict, Any


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def convert_timestamp(timestamp: str or int) -> str or None:
    """ Converts epoch timestamp into human-readable time

    Args:
        timestamp: epoch timestamp in seconds
    Returns:
        String time in the format YYYY-mm-dd hh:mm:ss
    """

    if timestamp:
        if isinstance(timestamp, str):
            timestamp = timestamp.split('.', 1)[0]

        return time.strftime('%Y-%m-%d %H:%M:%S %Z', time.gmtime(int(timestamp)))
    else:
        return None


def convert_to_dict(obj: Any) -> Dict:
    """ Returns a dictionary object from a dataclass object or a dict
    containing nested dataclass objects.

    Args:
        obj: dataclass object or dict
    Returns:
        Dictionary object
    """

    json_object = json.dumps(obj, sort_keys=True, cls=EnhancedJSONEncoder)
    return json.loads(json_object)


def deduplicate_results(input_list: List[Any]) -> List[Dict]:
    """ Removes duplicates where results are returned by multiple queries. This is done
    using the `watchman_id` field in the detection data to identify the same findings.

    The `watchman_id` is a hash that is generated for each finding from the match string and the
    timestamp, meaning the same message won't be returned multiple times.

    Args:
        input_list: List of dataclass objects
    Returns:
        List of JSON objects with duplicates removed
    """

    converted_dict_list = [convert_to_dict(t) for t in input_list]
    return list({match.get('watchman_id'): match for match in reversed(converted_dict_list)}.values())
