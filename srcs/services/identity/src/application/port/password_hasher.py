from typing import Protocol

from src.domain.value_objects.password_hash import PasswordHash


# Protocol in Python ≈ interface in C++,
class PasswordHasher(Protocol):
    def hash(self, plaintext: str) -> PasswordHash:
        """
        Hash a plaintext password
        """

    def verify(self, plaintext: str, password_hash: PasswordHash) -> bool:
        """
        Verify that a plaintext password matches a password hash
        """
