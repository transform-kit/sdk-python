"""Tests for pipeline validation — mirrors sdk/src/engine/validate.test.ts."""

from transformkit import (
    ConfigField,
    Edge,
    NodeInstance,
    Pipeline,
    create_default_registry,
    validate_pipeline,
)

registry = create_default_registry()


def _valid_pipeline() -> Pipeline:
    return Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="filter", type="image.filter", config={"extension": ConfigField(value="heic", editable=False)}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[
            Edge(source="input", target="filter"),
            Edge(source="filter", target="output"),
        ],
    )


def test_accepts_valid_pipeline():
    result = validate_pipeline(_valid_pipeline(), registry)
    assert result.valid
    assert len(result.errors) == 0


def test_rejects_missing_input():
    p = Pipeline(nodes=[NodeInstance(id="output", type="pipeline.output", config={})], edges=[])
    result = validate_pipeline(p)
    assert not result.valid
    assert any(e.code == "NO_INPUT" for e in result.errors)


def test_rejects_missing_output():
    p = Pipeline(nodes=[NodeInstance(id="input", type="pipeline.input", config={})], edges=[])
    result = validate_pipeline(p)
    assert not result.valid
    assert any(e.code == "NO_OUTPUT" for e in result.errors)


def test_detects_duplicate_ids():
    p = Pipeline(
        nodes=[
            NodeInstance(id="dupe", type="pipeline.input", config={}),
            NodeInstance(id="dupe", type="pipeline.output", config={}),
        ],
        edges=[Edge(source="dupe", target="dupe")],
    )
    result = validate_pipeline(p)
    assert any(e.code == "DUPLICATE_NODE_ID" for e in result.errors)


def test_detects_edge_missing_source():
    p = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[Edge(source="input", target="output"), Edge(source="ghost", target="output")],
    )
    result = validate_pipeline(p)
    assert any(e.code == "EDGE_MISSING_SOURCE" for e in result.errors)


def test_detects_edge_missing_target():
    p = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[Edge(source="input", target="output"), Edge(source="input", target="void")],
    )
    result = validate_pipeline(p)
    assert any(e.code == "EDGE_MISSING_TARGET" for e in result.errors)


def test_detects_input_no_outgoing():
    p = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="mid", type="image.filter", config={"extension": ConfigField(value="png", editable=False)}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[Edge(source="mid", target="output")],
    )
    result = validate_pipeline(p, registry)
    assert any(e.code == "INPUT_NO_OUTGOING" and e.node_id == "input" for e in result.errors)


def test_detects_output_no_incoming():
    p = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="mid", type="image.filter", config={"extension": ConfigField(value="png", editable=False)}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[Edge(source="input", target="mid")],
    )
    result = validate_pipeline(p, registry)
    assert any(e.code == "OUTPUT_NO_INCOMING" and e.node_id == "output" for e in result.errors)


def test_detects_cycles():
    p = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="a", type="image.filter", config={"extension": ConfigField(value="png", editable=False)}),
            NodeInstance(id="b", type="image.filter", config={"extension": ConfigField(value="png", editable=False)}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[
            Edge(source="input", target="a"),
            Edge(source="a", target="b"),
            Edge(source="b", target="a"),
            Edge(source="b", target="output"),
        ],
    )
    result = validate_pipeline(p)
    assert any(e.code == "CYCLE_DETECTED" for e in result.errors)


def test_detects_disconnected_middle_nodes():
    p = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="orphan", type="image.filter", config={"extension": ConfigField(value="png", editable=False)}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[Edge(source="input", target="output")],
    )
    result = validate_pipeline(p)
    assert any(e.code == "NO_INCOMING_EDGE" and e.node_id == "orphan" for e in result.errors)
    assert any(e.code == "NO_OUTGOING_EDGE" and e.node_id == "orphan" for e in result.errors)


def test_detects_unknown_node_types():
    p = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="bad", type="nonexistent.node", config={}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[Edge(source="input", target="bad"), Edge(source="bad", target="output")],
    )
    result = validate_pipeline(p, registry)
    assert any(e.code == "UNKNOWN_NODE_TYPE" for e in result.errors)


def test_no_type_check_without_registry():
    p = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="custom", type="anything.goes", config={}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[Edge(source="input", target="custom"), Edge(source="custom", target="output")],
    )
    result = validate_pipeline(p)
    assert not any(e.code == "UNKNOWN_NODE_TYPE" for e in result.errors)


def test_accepts_multi_output_branches_with_shared_convert():
    p = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="convert", type="image.convert", config={"format": ConfigField(value="png", editable=False)}),
            NodeInstance(id="a", type="pipeline.output", config={}),
            NodeInstance(id="b", type="pipeline.output", config={}),
        ],
        edges=[
            Edge(source="input", target="convert"),
            Edge(source="convert", target="a"),
            Edge(source="convert", target="b"),
        ],
    )
    result = validate_pipeline(p, registry)
    assert result.valid


def test_accepts_multi_output_when_one_branch_uses_strip_metadata():
    p = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="convert", type="image.convert", config={"format": ConfigField(value="png", editable=False)}),
            NodeInstance(id="strip", type="image.strip-metadata", config={"enabled": ConfigField(value=True, editable=True)}),
            NodeInstance(id="keep", type="pipeline.output", config={}),
            NodeInstance(id="stripped", type="pipeline.output", config={}),
        ],
        edges=[
            Edge(source="input", target="convert"),
            Edge(source="convert", target="keep"),
            Edge(source="convert", target="strip"),
            Edge(source="strip", target="stripped"),
        ],
    )
    result = validate_pipeline(p, registry)
    assert result.valid


def test_accepts_minimal_two_node_pipeline():
    p = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[Edge(source="input", target="output")],
    )
    result = validate_pipeline(p, registry)
    assert result.valid
