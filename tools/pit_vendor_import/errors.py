class VendorImportError(Exception):
    """Base class for signed vendor package failures."""


class ValidationError(VendorImportError):
    """Raised when signatures, files, schemas, or point-in-time metadata fail."""
