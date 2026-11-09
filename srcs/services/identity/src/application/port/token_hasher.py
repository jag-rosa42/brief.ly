from typing import Protocol


class TokenHasher(Protocol):
    """Hashes a token before it is stored, and again when it comes back.

    Identity never stores a token as is, only its hash: someone who reads the
    database can't use what they find there. When a client sends the token
    back (a refresh token, for example), we hash what we received and compare
    the result with the stored hash, or look the token up by it.

    Storing and comparing must hash the same way, so both go through this
    port.

    Not for passwords: they need a slow hash (PasswordHasher, Argon2).
    """

    def hash(self, token: str) -> str:
        """
        Hash a token, the same way every time for the same input
        """
