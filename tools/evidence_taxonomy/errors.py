class TaxonomyError(Exception):
    """Base class for evidence-taxonomy failures."""


class ValidationError(TaxonomyError):
    """Raised when a taxonomy specification or evidence model is invalid."""
