class SymbolicEvidenceError(Exception):
    """Base class for symbolic evidence synthesis failures."""


class ValidationError(SymbolicEvidenceError):
    """Raised when an attack corpus or certificate is malformed."""
