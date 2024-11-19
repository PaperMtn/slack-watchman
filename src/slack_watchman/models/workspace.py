from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(slots=True)
class Workspace:
    """Class that defines Workspace objects. Workspaces are collections
    of conversations in a Slack Enterprise Organisation."""

    id: str
    name: str
    domain: str
    url: str
    email_domain: str
    is_verified: Optional[bool] = None
    discoverable: Optional[bool] = None
    enterprise_id: Optional[str] = None
    enterprise_domain: Optional[str] = None
    enterprise_name: Optional[str] = None

    def __post_init__(self):
        """Validate types of fields after initialisation."""
        expected_types = {
            'id': str,
            'name': str,
            'domain': str,
            'url': str,
            'email_domain': str,
            'is_verified': (bool, type(None)),
            'discoverable': (bool, type(None)),
            'enterprise_id': (str, type(None)),
            'enterprise_domain': (str, type(None)),
            'enterprise_name': (str, type(None)),
        }

        for field_name, expected_type in expected_types.items():
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, expected_type):
                raise TypeError(
                    f'Expected `{field_name}` to be of type {expected_type}, '
                    f'received {type(value).__name__}'
                )

def create_from_dict(workspace_dict: Dict) -> Workspace:
    """ Return a Workspace object based off an input dictionary

    Args:
        workspace_dict: dictionary/JSON formatted representation of the
            workspace.
    Returns:
        Workspace object representing the workspace
    """

    return Workspace(
        id=workspace_dict.get('id'),
        name=workspace_dict.get('name'),
        domain=workspace_dict.get('domain'),
        email_domain=workspace_dict.get('email_domain'),
        is_verified=workspace_dict.get('is_verified'),
        discoverable=workspace_dict.get('discoverable'),
        enterprise_id=workspace_dict.get('enterprise_id'),
        enterprise_domain=workspace_dict.get('enterprise_domain'),
        enterprise_name=workspace_dict.get('enterprise_name'),
        url=workspace_dict.get('url')
    )
