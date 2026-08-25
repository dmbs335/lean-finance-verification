class AnytimePolicyMonitorError(Exception):
    """Base class for anytime policy-monitor failures."""


class ValidationError(AnytimePolicyMonitorError):
    """Raised when an anytime monitor model or report is malformed."""
