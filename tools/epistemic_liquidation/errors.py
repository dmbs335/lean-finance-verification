class EpistemicLiquidationError(Exception):
    """Base class for epistemic-liquidation model failures."""


class ValidationError(EpistemicLiquidationError):
    """Raised when a scenario or report is malformed."""
