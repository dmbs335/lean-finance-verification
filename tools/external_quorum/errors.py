class ExternalQuorumError(Exception):
    """Base class for external evidence verification failures."""


class ValidationError(ExternalQuorumError):
    """Raised when signatures, inclusion proofs, or quorum policy fail."""
