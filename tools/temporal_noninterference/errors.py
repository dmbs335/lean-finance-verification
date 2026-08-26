class TemporalNoninterferenceError(Exception):
    """Base class for temporal-noninterference failures."""


class ValidationError(TemporalNoninterferenceError):
    """Raised when a benchmark, mutation, engine, or report is malformed."""
