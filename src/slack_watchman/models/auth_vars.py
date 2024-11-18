from dataclasses import dataclass
from typing import Optional, List


@dataclass
class AuthVars:
    """ Class for managing authentication and configuration variables """
    token: Optional[str] | None
    cookie: Optional[str] | None
    url: Optional[str] | None
    disabled_signatures: Optional[List[str]] | None
    cookie_auth: bool
