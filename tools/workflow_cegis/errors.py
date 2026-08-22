class CegisError(Exception):
    """Base class for workflow CEGIS failures."""


class ValidationError(CegisError):
    """Raised when a workflow model violates its finite semantics."""
