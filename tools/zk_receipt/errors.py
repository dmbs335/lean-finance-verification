class ZKReceiptError(Exception):
    """Base class for private-predicate receipt failures."""


class ValidationError(ZKReceiptError):
    """Raised when group, commitment, proof, signature, or policy checks fail."""
