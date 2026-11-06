from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceClient:
    """A backend service allowed to get service tokens.

    OAuth 2.0 calls it a "client": a program that asks for tokens on its own
    behalf, with no user involved (the client credentials grant, RFC 6749
    §4.4).

    `allowed_scopes` says, for each audience (the service the token is for),
    which scopes the client may ask for. An audience missing from it is
    refused. The client's secret is not here: secrets live in Compose secrets,
    never in code.
    """

    client_id: str
    allowed_scopes: Mapping[str, frozenset[str]]

    def may_request(self, audience: str, scopes: frozenset[str]) -> bool:
        """True when every requested scope is allowed for this audience.

        An empty request is refused: the client must say what it needs
        (least privilege).
        """
        if not scopes:
            return False
        return scopes <= self.allowed_scopes.get(audience, frozenset())