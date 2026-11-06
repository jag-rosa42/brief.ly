from enum import StrEnum


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
    SERVICE = "service" # A backend service calling another one, with no user
