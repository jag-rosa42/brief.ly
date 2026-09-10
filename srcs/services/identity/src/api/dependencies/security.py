from typing import Annotated

from fastapi import Depends

from src.application.port.password_hasher import PasswordHasher
from src.infrastructure.security.password_hasher import PwdlibPasswordHasher


# ---------------------------------------------------------------------------
# Password Hasher
# ---------------------------------------------------------------------------
def get_password_hasher() -> PasswordHasher:
    return PwdlibPasswordHasher()


PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]
