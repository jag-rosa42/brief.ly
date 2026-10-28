import pytest

from shared_auth.domain.exceptions import InsufficientScopeError
from shared_auth.domain.scopes import ensure_scopes
from tests.fixtures.factory import (
    READ_SCOPE,
    WRITE_SCOPE,
    build_service_principal,
    build_user_principal,
)


class TestEnsureScopes:
    def test_passes_with_every_scope(self) -> None:
        ensure_scopes(build_service_principal("a", "b", "c"), ["a", "b"])

    def test_passes_when_nothing_is_required(self) -> None:
        ensure_scopes(build_service_principal(), [])

    def test_works_for_a_user_principal(self) -> None:
        # Public API tokens carry scopes too.
        ensure_scopes(build_user_principal(READ_SCOPE, WRITE_SCOPE), [WRITE_SCOPE])

    def test_names_the_missing_scopes(self) -> None:
        with pytest.raises(InsufficientScopeError) as error:
            ensure_scopes(build_service_principal("a"), ["a", "b", "c"])

        assert error.value.missing == {"b", "c"}
        assert str(error.value) == "Missing scope: b c"
