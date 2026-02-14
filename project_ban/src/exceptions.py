"""Error taxonomy for Project B.A.N.

Separates errors into Transient (retriable) and Deterministic (fix required)
categories for AIOps-ready observability.
"""

class BanError(Exception):
    """Base class for all B.A.N. exceptions."""


class TransientError(BanError):
    """An error that is likely to resolve on retry (e.g. network timeout)."""


class DeterministicError(BanError):
    """An error that requires code or configuration changes to fix."""
