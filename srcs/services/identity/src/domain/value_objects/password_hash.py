from dataclasses import dataclass

from src.domain.exception import InvalidPasswordHash


@dataclass(frozen=True, slots=True)
class PasswordHash:
    value: str

    def __post_init__(self):
        if not self.value:
            raise InvalidPasswordHash("Password can not be empty")
