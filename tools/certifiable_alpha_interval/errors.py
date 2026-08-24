class CertifiableAlphaIntervalError(Exception):
    """Base class for certifiable-alpha interval failures."""


class ValidationError(CertifiableAlphaIntervalError):
    """Raised when an interval model, evidence set, or report is malformed."""
