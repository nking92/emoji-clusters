"""Public API for emoji_clusters."""

from .core import (
    Cluster,
    Kind,
    classify,
    cluster_boundaries,
    cluster_index_at,
    count_clusters,
    iter_clusters,
    split,
    truncate,
)

__all__ = [
    "Cluster",
    "Kind",
    "classify",
    "cluster_boundaries",
    "cluster_index_at",
    "count_clusters",
    "iter_clusters",
    "split",
    "truncate",
]

__version__ = "0.2.0"
