"""A client to the FAIRsharing API."""

from .api import FairsharingClient, ensure_fairsharing, get_fairsharing_to_orcids, load_fairsharing

__all__ = [
    "FairsharingClient",
    "ensure_fairsharing",
    "get_fairsharing_to_orcids",
    "load_fairsharing",
]
