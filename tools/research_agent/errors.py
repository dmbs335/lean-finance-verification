class ResearchAgentError(Exception):
    """Base class for bounded research-agent failures."""


class ValidationError(ResearchAgentError):
    """Raised when a plan, gate, or report is malformed."""
