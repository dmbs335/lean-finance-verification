class CertificateCompositionError(Exception):
    """Base class for certificate-composition failures."""


class ValidationError(CertificateCompositionError):
    """Raised when a composition problem or report is malformed."""
