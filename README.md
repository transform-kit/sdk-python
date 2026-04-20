# @transformkit/sdk (Python)

Node-based media pipeline engine for Python — a faithful port of the [TypeScript SDK](https://www.npmjs.com/package/@transform-kit/sdk).

## Install

```bash
pip install transformkit
```

## Quick start

```python
import asyncio

from transformkit import (
    ConfigField,
    Edge,
    NodeInstance,
    Pipeline,
    create_context,
    create_default_registry,
    create_mock_transport,
    run_pipeline,
    validate_pipeline,
)

pipeline = Pipeline(
    nodes=[
        NodeInstance(id="in", type="pipeline.input"),
        NodeInstance(id="convert", type="image.convert", config={
            "format": ConfigField(value="png", editable=False),
        }),
        NodeInstance(id="out", type="pipeline.output"),
    ],
    edges=[
        Edge(source="in", target="convert"),
        Edge(source="convert", target="out"),
    ],
)

result = validate_pipeline(pipeline, create_default_registry())
assert result.valid


async def main():
    transport = create_mock_transport()
    ctx = create_context(b"\xff" * 1024, "heic")
    outputs = await run_pipeline(pipeline, create_default_registry(), transport, ctx)
    for out in outputs:
        print(out.metadata.output_file_name, len(out.file))

asyncio.run(main())
```

## Metadata stripping

Metadata handling is an explicit graph operation, not a flag on the output. Drop
`image.strip-metadata`, `video.strip-metadata`, or `audio.strip-metadata` into
the branch that should come out clean; leave other branches untouched to keep
EXIF/XMP/IPTC/container tags. Each strip node has one boolean config field,
`enabled` (default `True`) — set to `False` to bypass the node without removing
it from the graph.

Transports implement the `operation: "strip-metadata"` payload as a lossless
pass when possible (`ffmpeg -c copy -map_metadata -1` for video/audio;
chunk-walk or re-emit without tag data for images). **ICC color profiles are
always preserved** to avoid unintended color shifts.

Because stripping is a regular node, two `pipeline.output` nodes can share an
upstream `image.convert` and differ only in whether a `strip-metadata` node
sits before one of them — no per-output flag propagation, no conflict error.

## License

MIT
