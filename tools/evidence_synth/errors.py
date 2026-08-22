class SynthesisError(Exception):
    """Base class for evidence-synthesis failures."""


class ValidationError(SynthesisError):
    """Raised when a model or certificate violates its contract."""
