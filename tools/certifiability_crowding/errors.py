class CertifiabilityCrowdingError(Exception):
    """Base class for certifiability-crowding failures."""


class ValidationError(CertifiabilityCrowdingError):
    """Raised when a scenario or report is malformed."""
