class InfrastructureError(Exception):
    """
    Raised when a dependency a service relies on (database, cache, another service, etc.)
    is unreachable or misbehaving.
    Distinct from DomainError: this is never a business-rule violation,
    it's an operational failure.
    """
    def __init__(self, message: str = "A required service dependency is unavailable."):
        super().__init__(message)