class BeliefControlError(Exception):
    """Base class for belief-control failures."""


class ValidationError(BeliefControlError):
    """Raised when a belief-control model or report is malformed."""
