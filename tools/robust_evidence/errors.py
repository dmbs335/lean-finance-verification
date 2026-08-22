class RobustEvidenceError(Exception):
    """Base class for robust evidence synthesis failures."""


class ValidationError(RobustEvidenceError):
    """Raised when a fault policy or certificate violates its contract."""
