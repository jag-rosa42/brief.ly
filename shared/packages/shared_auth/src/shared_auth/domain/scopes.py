"""
Authorization: may this caller do this?

Authentication (application/authenticator.py) answers "who is calling?" and
needs a token. This rule only needs the principal it produced.
"""

from collections.abc import Iterable

from shared_auth.domain.exceptions import InsufficientScopeError
from shared_auth.domain.principals import Principal


def ensure_scopes(principal: Principal, required: Iterable[str]) -> None:
    """Raise InsufficientScopeError unless the principal holds every scope."""
    missing: frozenset[str] = frozenset(required) - principal.scopes
    if missing:
        raise InsufficientScopeError(missing)
