class TemporalNoninterferenceError(Exception):
    """Base class for temporal-noninterference failures."""


class ValidationError(TemporalNoninterferenceError):
    """Raised when a temporal model or report is malformed."""
