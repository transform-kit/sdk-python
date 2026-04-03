"""Kahn's algorithm: topological sort of a directed acyclic graph."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class KahnResult:
    sorted: list[str]
    has_cycle: bool


def kahn_topological_sort(
    nodes: list[dict[str, str]],
    edges: list[dict[str, str]],
) -> KahnResult:
    """Topological sort using Kahn's algorithm.

    Args:
        nodes: List of dicts with ``id`` keys.
        edges: List of dicts with ``source`` and ``target`` keys.

    Returns:
        Sorted node IDs and whether a cycle was detected.
    """
    in_degree: dict[str, int] = {}
    adj: dict[str, list[str]] = {}

    for node in nodes:
        nid = node["id"]
        in_degree[nid] = 0
        adj[nid] = []

    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        if src not in in_degree or tgt not in in_degree:
            continue
        in_degree[tgt] = in_degree.get(tgt, 0) + 1
        adj[src].append(tgt)

    queue: deque[str] = deque()
    for nid, deg in in_degree.items():
        if deg == 0:
            queue.append(nid)

    sorted_ids: list[str] = []
    while queue:
        cur = queue.popleft()
        sorted_ids.append(cur)
        for nb in adj.get(cur, []):
            in_degree[nb] = in_degree.get(nb, 1) - 1
            if in_degree[nb] == 0:
                queue.append(nb)

    return KahnResult(sorted=sorted_ids, has_cycle=len(sorted_ids) < len(nodes))
