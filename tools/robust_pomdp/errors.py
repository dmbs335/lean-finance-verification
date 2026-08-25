class RobustPomdpError(Exception):
    """Base class for robust-POMDP failures."""


class ValidationError(RobustPomdpError):
    """Raised when a finite robust-POMDP model or report is malformed."""
