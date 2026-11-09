import hashlib


class Sha256TokenHasher:
    """SHA-256, written as 64 hexadecimal characters.

    A fast hash is fine here, unlike for passwords (PwdlibPasswordHasher).
    A password is short and chosen by a person: someone who steals its hash
    can try likely passwords until one gives the same hash, so passwords need
    a slow hash that makes each try expensive. The tokens hashed here are
    long and unpredictable: there is no list of likely tokens to try, so a
    fast hash is safe, and it keeps every check cheap.
    """

    def hash(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
