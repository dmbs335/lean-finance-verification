class SelectiveReceiptError(Exception):
    """Base class for selective-receipt failures."""


class ValidationError(SelectiveReceiptError):
    """Raised when policy, commitment, disclosure, or signature checks fail."""
