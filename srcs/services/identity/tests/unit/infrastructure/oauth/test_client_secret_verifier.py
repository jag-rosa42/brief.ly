from pathlib import Path

from src.infrastructure.oauth.client_secret_verifier import (
    SecretFileClientSecretVerifier,
)
from tests.fixtures.oauth import TEST_CLIENT_ID, TEST_CLIENT_SECRET


def build_verifier(secrets_dir: Path) -> SecretFileClientSecretVerifier:
    return SecretFileClientSecretVerifier(
        secrets_dir=secrets_dir,
        known_client_ids=[TEST_CLIENT_ID],
    )


class TestSecretFileClientSecretVerifier:
    def test_accepts_the_secret_from_the_file(self, client_secrets_dir: Path) -> None:
        assert build_verifier(client_secrets_dir).verify(
            TEST_CLIENT_ID, TEST_CLIENT_SECRET
        )

    def test_reads_the_file_named_after_the_client_with_underscores(
        self, client_secrets_dir: Path
    ) -> None:
        # "test-client" -> test_client_client_secret, like ai_processing_client_secret.
        assert (client_secrets_dir / "test_client_client_secret").is_file()

    def test_refuses_a_wrong_secret(self, client_secrets_dir: Path) -> None:
        assert not build_verifier(client_secrets_dir).verify(TEST_CLIENT_ID, "wrong")

    def test_refuses_a_secret_that_only_starts_right(
        self, client_secrets_dir: Path
    ) -> None:
        assert not build_verifier(client_secrets_dir).verify(
            TEST_CLIENT_ID, TEST_CLIENT_SECRET[:-1]
        )

    def test_ignores_a_final_newline_in_the_file(self, tmp_path: Path) -> None:
        (tmp_path / "test_client_client_secret").write_text(f"{TEST_CLIENT_SECRET}\n")

        assert build_verifier(tmp_path).verify(TEST_CLIENT_ID, TEST_CLIENT_SECRET)

    def test_refuses_a_client_without_a_secret_file(self, tmp_path: Path) -> None:
        assert not build_verifier(tmp_path).verify(TEST_CLIENT_ID, TEST_CLIENT_SECRET)

    def test_refuses_a_client_with_an_empty_secret_file(self, tmp_path: Path) -> None:
        (tmp_path / "test_client_client_secret").write_text("")

        assert not build_verifier(tmp_path).verify(TEST_CLIENT_ID, "")

    def test_refuses_an_unknown_client_even_if_a_file_matches(
        self, client_secrets_dir: Path
    ) -> None:
        (client_secrets_dir / "intruder_client_secret").write_text("intruder-secret")

        assert not build_verifier(client_secrets_dir).verify(
            "intruder", "intruder-secret"
        )

    def test_never_builds_a_path_from_an_unknown_client_id(self, tmp_path: Path) -> None:
        # Without the known-ID check, this ID would point at another secret file.
        secrets_dir: Path = tmp_path / "secrets"
        secrets_dir.mkdir()
        (tmp_path / "jwt_private_key_client_secret").write_text("private")

        assert not build_verifier(secrets_dir).verify("../jwt_private_key", "private")
