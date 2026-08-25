class SafeTreeSearchError(Exception):
    """Base class for safe tree-search failures."""


class ValidationError(SafeTreeSearchError):
    """Raised when a finite tree-search model or report is malformed."""
