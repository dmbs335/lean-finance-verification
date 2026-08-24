class PolicyMonitorError(Exception):
    """Base class for policy-monitor failures."""


class ValidationError(PolicyMonitorError):
    """Raised when a monitoring plan or report is malformed."""
