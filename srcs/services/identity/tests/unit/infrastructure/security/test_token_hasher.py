import hashlib

from src.infrastructure.security.token_hasher import Sha256TokenHasher


class TestSha256TokenHasher:
    def test_hash_is_the_sha256_of_the_token_in_hexadecimal(self) -> None:
        token: str = "tr_some-key-or-refresh-token"

        hashed: str = Sha256TokenHasher().hash(token)

        assert hashed == hashlib.sha256(token.encode()).hexdigest()
        assert len(hashed) == 64
        assert hashed != token

    def test_same_token_gives_the_same_hash(self) -> None:
        # Required to find a stored token again by hashing what comes back.
        assert Sha256TokenHasher().hash("token") == Sha256TokenHasher().hash("token")

    def test_different_tokens_give_different_hashes(self) -> None:
        assert Sha256TokenHasher().hash("token-a") != Sha256TokenHasher().hash("token-b")
