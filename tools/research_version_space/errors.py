class ResearchVersionSpaceError(Exception):
    """Base class for research-version-space failures."""


class ValidationError(ResearchVersionSpaceError):
    """Raised when a world model or report is malformed."""
