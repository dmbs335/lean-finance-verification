class PnlExplainClosureError(Exception):
    """Base class for PnL-explain closure failures."""


class ValidationError(PnlExplainClosureError):
    """Raised when a model, case, or report is malformed."""
