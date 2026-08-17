from pwdlib import PasswordHash as PwdlibPasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from src.domain.value_objects.password_hash import PasswordHash


class PwdlibPasswordHasher:
    def __init__(self):
        self._password_hasher: PwdlibPasswordHash = PwdlibPasswordHash(
            (Argon2Hasher(),)
        )

    def hash(self, plaintext: str) -> PasswordHash:
        hashed_password: str = self._password_hasher.hash(plaintext)
        return PasswordHash(hashed_password)

    def verify(self, plaintext: str, password_hash: PasswordHash) -> bool:
        return self._password_hasher.verify(plaintext, password_hash.value)
