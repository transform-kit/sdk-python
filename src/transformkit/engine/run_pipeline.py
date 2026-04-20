"""Pipeline execution engine."""

from __future__ import annotations

from ..pipeline_node_defaults import merge_pipeline_node_config
from ..types import ExecutionContext, Pipeline, Transport
from .kahn import kahn_topological_sort
from .registry import NodeRegistry


async def run_pipeline(
    pipeline: Pipeline,
    registry: NodeRegistry,
    transport: Transport,
    initial_ctx: ExecutionContext,
) -> list[ExecutionContext]:
    """Execute a pipeline against an initial context and return all output contexts.

    1. Validates the graph has input and output nodes.
    2. Topologically sorts nodes (rejects cycles).
    3. Executes each node, propagating context or skip status.
    4. Collects and returns contexts from ``output`` results.

    Raises:
        RuntimeError: If no input/output nodes, cycle detected, or unknown node type.
    """
    if not any(n.type == "pipeline.input" for n in pipeline.nodes):
        raise RuntimeError("Pipeline must have at least one Input node.")
    if not any(n.type == "pipeline.output" for n in pipeline.nodes):
        raise RuntimeError("Pipeline must have at least one Output node.")

    node_dicts = [{"id": n.id, "type": n.type} for n in pipeline.nodes]
    edge_dicts = [{"source": e.source, "target": e.target} for e in pipeline.edges]
    result = kahn_topological_sort(node_dicts, edge_dicts)
    if result.has_cycle:
        raise RuntimeError("Pipeline contains a cycle \u2014 nodes cannot reference each other in a loop.")

    node_map = {n.id: n for n in pipeline.nodes}

    incoming: dict[str, list[str]] = {n.id: [] for n in pipeline.nodes}
    for edge in pipeline.edges:
        if edge.target in incoming:
            incoming[edge.target].append(edge.source)

    state: dict[str, tuple[ExecutionContext, bool]] = {}
    outputs: list[ExecutionContext] = []

    for node_id in result.sorted:
        node = node_map[node_id]
        definition = registry.get(node.type)
        if definition is None:
            raise RuntimeError(f"Unknown node type: {node.type}")

        upstream_ids = incoming.get(node_id, [])

        all_upstream_skipped = (
            len(upstream_ids) > 0
            and all(node_id_ in state and state[node_id_][1] for node_id_ in upstream_ids)
        )
        if all_upstream_skipped:
            state[node_id] = (initial_ctx, True)
            continue

        input_ctx = initial_ctx
        for uid in upstream_ids:
            up = state.get(uid)
            if up is not None and not up[1]:
                input_ctx = up[0]
                break

        merged_config = merge_pipeline_node_config(node.type, node.config)
        node_result = await definition.execute(input_ctx, merged_config, transport)

        if node_result.status == "skip":
            state[node_id] = (input_ctx, True)
            continue

        state[node_id] = (node_result.ctx, False)

        if node_result.status == "output":
            outputs.append(node_result.ctx)

    return outputs


async def process_files(
    files: list[ExecutionContext],
    pipeline: Pipeline,
    registry: NodeRegistry,
    transport: Transport,
) -> list[ExecutionContext]:
    """Run a pipeline once per file and concatenate all outputs."""
    all_outputs: list[ExecutionContext] = []
    for ctx in files:
        outputs = await run_pipeline(pipeline, registry, transport, ctx)
        all_outputs.extend(outputs)
    return all_outputs
