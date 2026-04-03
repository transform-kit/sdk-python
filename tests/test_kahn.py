"""Tests for Kahn's topological sort — mirrors sdk/src/engine/kahn.test.ts."""

from transformkit.engine.kahn import kahn_topological_sort


def test_sorts_linear_chain():
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}]
    result = kahn_topological_sort(nodes, edges)
    assert not result.has_cycle
    assert result.sorted == ["a", "b", "c"]


def test_sorts_diamond_shape():
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}]
    edges = [
        {"source": "a", "target": "b"},
        {"source": "a", "target": "c"},
        {"source": "b", "target": "d"},
        {"source": "c", "target": "d"},
    ]
    result = kahn_topological_sort(nodes, edges)
    assert not result.has_cycle
    assert result.sorted[0] == "a"
    assert result.sorted[-1] == "d"
    assert len(result.sorted) == 4


def test_detects_simple_cycle():
    nodes = [{"id": "a"}, {"id": "b"}]
    edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "a"}]
    result = kahn_topological_sort(nodes, edges)
    assert result.has_cycle


def test_single_node_no_edges():
    result = kahn_topological_sort([{"id": "solo"}], [])
    assert not result.has_cycle
    assert result.sorted == ["solo"]


def test_ignores_edges_referencing_nonexistent_nodes():
    nodes = [{"id": "a"}, {"id": "b"}]
    edges = [{"source": "a", "target": "b"}, {"source": "ghost", "target": "b"}]
    result = kahn_topological_sort(nodes, edges)
    assert not result.has_cycle
    assert len(result.sorted) == 2
