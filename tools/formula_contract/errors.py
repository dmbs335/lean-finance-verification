class FormulaContractError(Exception):
    """Base class for formula-contract failures."""


class ValidationError(FormulaContractError):
    """Raised when a formula problem or report is malformed."""
