class AutonomousPipelineError(Exception):
    """Base class for autonomous-pipeline failures."""


class ValidationError(AutonomousPipelineError):
    """Raised when a pipeline model or report is malformed."""
