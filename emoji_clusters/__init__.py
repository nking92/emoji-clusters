"""Public API for emoji_clusters."""

from .core import Cluster, Kind, classify, iter_clusters, split

__all__ = ["Cluster", "Kind", "classify", "iter_clusters", "split"]

__version__ = "0.1.0"
