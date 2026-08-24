class FakeAlphaError(Exception):
    """Base class for fake-alpha benchmark failures."""


class ValidationError(FakeAlphaError):
    """Raised when a benchmark, candidate, or report is malformed."""
