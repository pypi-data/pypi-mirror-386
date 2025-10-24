from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from rich.console import Console
from rich.syntax import Syntax

from .base import PrettyModel

class Token(PrettyModel):
    """Información de token OIDC"""
    access_token: str
    expires_in: int
    refresh_expires_in: int
    refresh_token: str = Field(None)
    token_type: str
    id_token: Optional[str] = None
    session_state: Optional[str] = None
    scope: Optional[str] = None

class AccessToken(PrettyModel):
    """Payload del access token OIDC"""
    exp: int
    iat: int
    jti: str
    iss: str
    aud: str | List[str]
    sub: str
    typ: str
    azp: str
    session_state: str = Field(None)
    acr: str = Field(None)
    realm_access: Optional[Dict] = None
    resource_access: Optional[Dict] = None
    scope: Optional[str] = None
    email_verified: Optional[bool] = None
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
    rls: Dict[str, Dict[str, List[str | Any]]] = Field(default_factory=dict)


class UserInfo(PrettyModel):
    """Información de usuario desde OIDC"""
    sub: str
    preferred_username: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    groups: Optional[list] = None
    roles: Optional[list] = None

