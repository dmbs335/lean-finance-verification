class EvidencePortfolioError(Exception):
    """Base class for evidence-adjusted portfolio failures."""


class ValidationError(EvidencePortfolioError):
    """Raised when a portfolio problem or report is malformed."""
