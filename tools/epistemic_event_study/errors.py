class EpistemicEventStudyError(Exception):
    """Base class for epistemic event-study failures."""


class ValidationError(EpistemicEventStudyError):
    """Raised when a registered plan, pair, or report is malformed."""
