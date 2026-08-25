class ProspectiveBacktestError(Exception):
    """Base class for prospective-backtest failures."""


class ValidationError(ProspectiveBacktestError):
    """Raised when an admission package or report is malformed."""
