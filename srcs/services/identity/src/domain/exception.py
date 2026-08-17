"""
Domain Layer errors.
"""

class DomainError(Exception):
    pass

class InvalidEmail(DomainError):
    pass

class InvalidPasswordHash(DomainError):
    pass

class EmailAlreadyRegisteredError(DomainError):
    pass
