class MultiClaimError(Exception):
    """Base class for multi-claim synthesis failures."""


class ValidationError(MultiClaimError):
    """Raised when a finite multi-claim model is malformed."""
