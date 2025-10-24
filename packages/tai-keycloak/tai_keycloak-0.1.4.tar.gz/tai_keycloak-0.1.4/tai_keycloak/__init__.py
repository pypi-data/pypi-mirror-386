"""tai-keycloak package"""

from .service import (
    KeycloakClient, KeycloakAsyncAPIClient, KeycloakSyncAPIClient,
    User, Role, Group, Client, Realm,
    UsersProfile, UsersProfileAttribute,
    ClientMapper, ClientMapperConfig
)

__all__ = [
    "KeycloakClient", "KeycloakAsyncAPIClient", "KeycloakSyncAPIClient",
    "User", "Role", "Group", "Client", "Realm",
    "UsersProfile", "UsersProfileAttribute",
    "ClientMapper", "ClientMapperConfig"
]

kc = KeycloakClient()