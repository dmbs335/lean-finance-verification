class TraceRefinementError(Exception):
    """Base class for observed-trace model refinement failures."""


class ValidationError(TraceRefinementError):
    """Raised when a trace lacks the observations required for sound refinement."""
