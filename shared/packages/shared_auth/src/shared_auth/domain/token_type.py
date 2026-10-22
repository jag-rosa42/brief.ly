from enum import StrEnum


class TokenType(StrEnum):
    ACCESS = "access" # used by either browser or public API
    REFRESH = "refresh" # only Identity accepts it, never a service
    SERVICE = "service" # a service acting without a user
