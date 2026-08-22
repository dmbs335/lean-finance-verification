class ModelFamilyError(Exception):
    """Base class for model-family synthesis failures."""


class ValidationError(ModelFamilyError):
    """Raised when a finite version-space model is malformed."""
