class MctsSpibbError(Exception):
    """Base class for MCTS-SPIBB planner failures."""


class ValidationError(MctsSpibbError):
    """Raised when a planner contract or report is malformed."""
