class ExecutionHarnessError(Exception):
    """Base class for proof-carrying execution failures."""


class ValidationError(ExecutionHarnessError):
    """Raised when an execution model or report is malformed."""
