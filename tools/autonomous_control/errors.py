class AutonomousControlError(Exception):
    """Base class for autonomous-control failures."""


class ValidationError(AutonomousControlError):
    """Raised when a finite control model or report is malformed."""
