from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email
from email_validator.types import ValidatedEmail

from src.domain.exception import InvalidEmail


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        try:
            result: ValidatedEmail = validate_email(
                self.value, check_deliverability=False
            )
        except EmailNotValidError as e:
            raise InvalidEmail() from e

        object.__setattr__(
            self,
            "value",
            result.normalized,
        )
