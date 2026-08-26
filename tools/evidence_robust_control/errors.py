class EvidenceRobustControlError(Exception):
    """Base class for robust-control failures."""


class ValidationError(EvidenceRobustControlError):
    """Raised when a robust-control model or report is malformed."""
