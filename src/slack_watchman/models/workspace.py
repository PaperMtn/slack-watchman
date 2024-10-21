from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(slots=True)
class Workspace(object):
    """ Class that defines Workspaces objects. Workspaces are collections
    of conversations in a Slack Enterprise Organisation"""

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
