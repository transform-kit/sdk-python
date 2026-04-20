"""Tests for run_pipeline / process_files — mirrors sdk/src/engine/run-pipeline.test.ts."""

import pytest

from transformkit import (
    ConfigField,
    Edge,
    NodeInstance,
    Pipeline,
    create_context,
    create_default_registry,
    create_mock_transport,
    process_files,
    run_pipeline,
)

registry = create_default_registry()
transport = create_mock_transport(0)


def _mock_file(extension: str, size: int = 1024):
    ctx = create_context(b"\xff" * size, extension)
    ctx.metadata.source_file_name = f"test-file.{extension}"
    return ctx


def _simple_pipeline(filter_type: str, filter_ext: str, convert_type: str, convert_format: str) -> Pipeline:
    return Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="filter", type=filter_type, config={"extension": ConfigField(value=filter_ext, editable=False)}),
            NodeInstance(id="convert", type=convert_type, config={"format": ConfigField(value=convert_format, editable=False)}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[
            Edge(source="input", target="filter"),
            Edge(source="filter", target="convert"),
            Edge(source="convert", target="output"),
        ],
    )


@pytest.mark.asyncio
async def test_processes_matching_file():
    pipeline = _simple_pipeline("image.filter", "heic", "image.convert", "png")
    ctx = _mock_file("heic")
    results = await run_pipeline(pipeline, registry, transport, ctx)
    assert len(results) == 1
    assert results[0].metadata.extension == "png"
    assert results[0].metadata.mime_type == "image/png"
    assert results[0].metadata.output_file_name is not None


@pytest.mark.asyncio
async def test_works_without_config_on_input_output():
    pipeline = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input"),
            NodeInstance(id="filter", type="image.filter", config={"extension": ConfigField(value="heic", editable=False)}),
            NodeInstance(id="convert", type="image.convert", config={"format": ConfigField(value="png", editable=False)}),
            NodeInstance(id="output", type="pipeline.output"),
        ],
        edges=[
            Edge(source="input", target="filter"),
            Edge(source="filter", target="convert"),
            Edge(source="convert", target="output"),
        ],
    )
    results = await run_pipeline(pipeline, registry, transport, _mock_file("heic"))
    assert len(results) == 1
    assert results[0].metadata.output_file_name is not None


@pytest.mark.asyncio
async def test_skips_non_matching_file():
    pipeline = _simple_pipeline("image.filter", "heic", "image.convert", "png")
    results = await run_pipeline(pipeline, registry, transport, _mock_file("png"))
    assert len(results) == 0


@pytest.mark.asyncio
async def test_heif_treated_as_heic():
    pipeline = _simple_pipeline("image.filter", "heic", "image.convert", "webp")
    results = await run_pipeline(pipeline, registry, transport, _mock_file("heif"))
    assert len(results) == 1
    assert results[0].metadata.extension == "webp"


@pytest.mark.asyncio
async def test_jpg_to_webp():
    pipeline = _simple_pipeline("image.filter", "jpg", "image.convert", "webp")
    results = await run_pipeline(pipeline, registry, transport, _mock_file("jpg"))
    assert len(results) == 1
    assert results[0].metadata.extension == "webp"
    assert results[0].metadata.mime_type == "image/webp"


@pytest.mark.asyncio
async def test_video_filter_convert():
    pipeline = _simple_pipeline("video.filter", "mov", "video.convert", "mp4")
    ctx = _mock_file("mov")
    ctx.metadata.mime_type = "video/quicktime"
    results = await run_pipeline(pipeline, registry, transport, ctx)
    assert len(results) == 1
    assert results[0].metadata.extension == "mp4"


@pytest.mark.asyncio
async def test_video_skip_non_matching():
    pipeline = _simple_pipeline("video.filter", "mov", "video.convert", "mp4")
    ctx = _mock_file("mp4")
    ctx.metadata.mime_type = "video/mp4"
    results = await run_pipeline(pipeline, registry, transport, ctx)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_audio_filter_convert():
    pipeline = _simple_pipeline("audio.filter", "wav", "audio.convert", "mp3")
    ctx = _mock_file("wav")
    ctx.metadata.mime_type = "audio/wav"
    results = await run_pipeline(pipeline, registry, transport, ctx)
    assert len(results) == 1
    assert results[0].metadata.extension == "mp3"


@pytest.mark.asyncio
async def test_output_filename_with_explicit_suffix():
    pipeline = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="output", type="pipeline.output", config={"nameSuffix": ConfigField(value="-copy", editable=True)}),
        ],
        edges=[Edge(source="input", target="output")],
    )
    results = await run_pipeline(pipeline, registry, transport, _mock_file("png"))
    assert len(results) == 1
    assert results[0].metadata.output_file_name == "test-file-copy.png"
    assert results[0].metadata.overwrite_source is False


@pytest.mark.asyncio
async def test_overwrite_source_when_suffix_empty():
    pipeline = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="output", type="pipeline.output", config={"nameSuffix": ConfigField(value="", editable=True)}),
        ],
        edges=[Edge(source="input", target="output")],
    )
    results = await run_pipeline(pipeline, registry, transport, _mock_file("png"))
    assert len(results) == 1
    assert results[0].metadata.output_file_name == "test-file.png"
    assert results[0].metadata.overwrite_source is True


@pytest.mark.asyncio
async def test_throws_no_input():
    pipeline = Pipeline(nodes=[NodeInstance(id="output", type="pipeline.output", config={})], edges=[])
    with pytest.raises(RuntimeError, match="Input node"):
        await run_pipeline(pipeline, registry, transport, _mock_file("png"))


@pytest.mark.asyncio
async def test_throws_no_output():
    pipeline = Pipeline(nodes=[NodeInstance(id="input", type="pipeline.input", config={})], edges=[])
    with pytest.raises(RuntimeError, match="Output node"):
        await run_pipeline(pipeline, registry, transport, _mock_file("png"))


@pytest.mark.asyncio
async def test_throws_on_cycle():
    pipeline = Pipeline(
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
    with pytest.raises(RuntimeError, match="cycle"):
        await run_pipeline(pipeline, registry, transport, _mock_file("png"))


class _RecordingTransport:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    async def convert(self, file: bytes, config: dict) -> bytes:
        self.payloads.append(dict(config))
        return bytes(file)


@pytest.mark.asyncio
async def test_image_strip_metadata_enabled_sends_operation_payload():
    rec = _RecordingTransport()
    pipeline = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="filter", type="image.filter", config={"extension": ConfigField(value="heic", editable=False)}),
            NodeInstance(id="convert", type="image.convert", config={"format": ConfigField(value="png", editable=False)}),
            NodeInstance(id="strip", type="image.strip-metadata", config={"enabled": ConfigField(value=True, editable=True)}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[
            Edge(source="input", target="filter"),
            Edge(source="filter", target="convert"),
            Edge(source="convert", target="strip"),
            Edge(source="strip", target="output"),
        ],
    )
    await run_pipeline(pipeline, registry, rec, _mock_file("heic"))  # type: ignore[arg-type]
    assert len(rec.payloads) == 2
    assert "operation" not in rec.payloads[0]
    assert rec.payloads[1]["operation"] == "strip-metadata"
    assert rec.payloads[1]["mediaType"] == "image"


@pytest.mark.asyncio
async def test_image_strip_metadata_disabled_is_passthrough():
    rec = _RecordingTransport()
    pipeline = Pipeline(
        nodes=[
            NodeInstance(id="input", type="pipeline.input", config={}),
            NodeInstance(id="filter", type="image.filter", config={"extension": ConfigField(value="heic", editable=False)}),
            NodeInstance(id="convert", type="image.convert", config={"format": ConfigField(value="png", editable=False)}),
            NodeInstance(id="strip", type="image.strip-metadata", config={"enabled": ConfigField(value=False, editable=True)}),
            NodeInstance(id="output", type="pipeline.output", config={}),
        ],
        edges=[
            Edge(source="input", target="filter"),
            Edge(source="filter", target="convert"),
            Edge(source="convert", target="strip"),
            Edge(source="strip", target="output"),
        ],
    )
    await run_pipeline(pipeline, registry, rec, _mock_file("heic"))  # type: ignore[arg-type]
    assert len(rec.payloads) == 1
    assert "operation" not in rec.payloads[0]


@pytest.mark.asyncio
async def test_process_files_multiple():
    pipeline = _simple_pipeline("image.filter", "heic", "image.convert", "png")
    files = [_mock_file("heic"), _mock_file("png"), _mock_file("heic")]
    results = await process_files(files, pipeline, registry, transport)
    assert len(results) == 2
    assert all(r.metadata.extension == "png" for r in results)


@pytest.mark.asyncio
async def test_process_files_no_match():
    pipeline = _simple_pipeline("image.filter", "heic", "image.convert", "png")
    files = [_mock_file("png"), _mock_file("jpg")]
    results = await process_files(files, pipeline, registry, transport)
    assert len(results) == 0
