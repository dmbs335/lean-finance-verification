from __future__ import annotations


class AdapterError(Exception):
    """Base class for deterministic adapter failures."""


class ValidationError(AdapterError):
    """Raised when an input violates a schema or semantic contract."""


class ExecutionError(AdapterError):
    """Raised when the empirical command fails or emits invalid output."""
