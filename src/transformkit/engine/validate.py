"""Pipeline validation without execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..types import Pipeline
from .kahn import kahn_topological_sort
from .registry import NodeRegistry


@dataclass
class ValidationError:
    """A single validation issue found in a pipeline."""

    code: str
    message: str
    node_id: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of :func:`validate_pipeline`."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)


def _pipeline_to_dicts(pipeline: Pipeline) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    nodes = [{"id": n.id, "type": n.type} for n in pipeline.nodes]
    edges = [{"source": e.source, "target": e.target} for e in pipeline.edges]
    return nodes, edges


def validate_pipeline(
    pipeline: Pipeline,
    registry: Optional[NodeRegistry] = None,
) -> ValidationResult:
    """Validate a pipeline's structure without executing it.

    Checks: duplicate IDs, missing input/output, dangling edges, unknown types,
    cycles, and disconnected nodes.
    """
    errors: list[ValidationError] = []
    nodes = pipeline.nodes
    edges = pipeline.edges

    id_set: set[str] = set()
    for node in nodes:
        if node.id in id_set:
            errors.append(ValidationError(
                code="DUPLICATE_NODE_ID",
                message=f'Duplicate node ID: "{node.id}"',
                node_id=node.id,
            ))
        id_set.add(node.id)

    if not any(n.type == "pipeline.input" for n in nodes):
        errors.append(ValidationError(code="NO_INPUT", message="Pipeline must have at least one Input node."))

    if not any(n.type == "pipeline.output" for n in nodes):
        errors.append(ValidationError(code="NO_OUTPUT", message="Pipeline must have at least one Output node."))

    for edge in edges:
        if edge.source not in id_set:
            errors.append(ValidationError(
                code="EDGE_MISSING_SOURCE",
                message=f'Edge references unknown source node "{edge.source}".',
            ))
        if edge.target not in id_set:
            errors.append(ValidationError(
                code="EDGE_MISSING_TARGET",
                message=f'Edge references unknown target node "{edge.target}".',
            ))

    if registry is not None:
        for node in nodes:
            if registry.get(node.type) is None:
                errors.append(ValidationError(
                    code="UNKNOWN_NODE_TYPE",
                    message=f'Unknown node type "{node.type}".',
                    node_id=node.id,
                ))

    node_dicts, edge_dicts = _pipeline_to_dicts(pipeline)
    result = kahn_topological_sort(node_dicts, edge_dicts)
    if result.has_cycle:
        errors.append(ValidationError(
            code="CYCLE_DETECTED",
            message="Pipeline contains a cycle \u2014 nodes cannot reference each other in a loop.",
        ))

    if len(nodes) > 1:
        has_incoming: set[str] = set()
        has_outgoing: set[str] = set()
        for edge in edges:
            if edge.source in id_set:
                has_outgoing.add(edge.source)
            if edge.target in id_set:
                has_incoming.add(edge.target)

        for node in nodes:
            is_input = node.type == "pipeline.input"
            is_output = node.type == "pipeline.output"

            if is_input and node.id not in has_outgoing:
                errors.append(ValidationError(
                    code="INPUT_NO_OUTGOING",
                    message="Input node has no outgoing connection.",
                    node_id=node.id,
                ))
            if is_output and node.id not in has_incoming:
                errors.append(ValidationError(
                    code="OUTPUT_NO_INCOMING",
                    message="Output node has no incoming connection.",
                    node_id=node.id,
                ))
            if not is_input and not is_output:
                if node.id not in has_incoming:
                    errors.append(ValidationError(
                        code="NO_INCOMING_EDGE",
                        message=f'"{node.type}" has no incoming connection.',
                        node_id=node.id,
                    ))
                if node.id not in has_outgoing:
                    errors.append(ValidationError(
                        code="NO_OUTGOING_EDGE",
                        message=f'"{node.type}" has no outgoing connection.',
                        node_id=node.id,
                    ))

    return ValidationResult(valid=len(errors) == 0, errors=errors)
