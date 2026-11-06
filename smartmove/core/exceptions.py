class SmartMoveError(Exception):
    """Base exception for SmartMove."""
    pass


class InvalidTransitionError(SmartMoveError):
    """Raised when a vehicle state transition is invalid."""
    pass


class VehicleUnavailableError(SmartMoveError):
    """Raised when a vehicle cannot be rented."""
    pass


class NoActiveRentalError(SmartMoveError):
    """Raised when trying to end a rental that does not exist."""
    pass


class RuleViolationError(SmartMoveError):
    """Raised when a city-specific rule is violated."""
    pass


class AuditWriteError(SmartMoveError):
    """Raised when audit logging fails."""
    pass


class IntegrityCheckError(SmartMoveError):
    """Raised when audit log integrity verification fails."""
    pass