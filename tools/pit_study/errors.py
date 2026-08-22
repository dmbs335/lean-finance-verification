class PITStudyError(Exception):
    """Base class for point-in-time study failures."""


class ValidationError(PITStudyError):
    """Raised when a study uses future, revised, or survivorship-filtered data."""
