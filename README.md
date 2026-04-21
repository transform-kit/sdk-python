# @transformkit/sdk (Python)

A pipeline engine for media processing. Define pipelines as JSON graphs, run them anywhere — server, desktop, or embedded in your own tooling. Python port of the [TypeScript SDK](https://www.npmjs.com/package/@transform-kit/sdk).

```
[Input] → [Filter: HEIC] → [Convert: PNG] → [Output]
```

Instead of writing one-off scripts that are tied to a specific tool, you describe **what** should happen as a portable pipeline and let the host decide **how**. The SDK handles graph execution. You provide a **Transport** — the backend that does the actual file conversion. Same pipeline, any backend.

## Installation

```bash
pip install transformkit
```

Requires **Python 3.10+**.

## Quick start

### Client (recommended)

The client manages a file queue and runs pipelines for you. Two modes:

**API mode** — sends files to a remote endpoint:

```python
from transformkit import AddFileInput, create_client

client = create_client(
    base_url="https://your-api.com",
    api_key="your_api_key",
)

client.add_files([
    AddFileInput(
        name="photo.heic",
        size=2_400_000,
        type="image/heic",
        file_bytes=file_bytes,
    ),
])

await client.process(pipeline)

def on_change(state):
    print(state.files, state.is_processing)

unsubscribe = client.subscribe(on_change)
```

**Transport mode** — runs the pipeline in-process:

```python
from transformkit import create_client

class MyTransport:
    async def convert(self, file: bytes, config: dict) -> bytes:
        return transformed_bytes

client = create_client(transport=MyTransport())
```

**Post-process hook** — both modes accept an optional `after_process_file(file, outputs)` callback that fires once per file after processing completes. Desktop hosts use it to write outputs to disk (in-place, next to the source, or into a chosen folder) without coupling the SDK to a filesystem.

```python
async def after_process_file(file, outputs):
    for o in outputs:
        write_bytes(target_for(file, o), o.file)

client = create_client(
    transport=MyTransport(),
    after_process_file=after_process_file,
)
```

### Low-level engine

For full control without the client queue:

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
)

registry = create_default_registry()
transport = create_mock_transport()

pipeline = Pipeline(
    nodes=[
        NodeInstance(id="1", type="pipeline.input"),
        NodeInstance(
            id="2",
            type="image.convert",
            config={
                "format": ConfigField(value="png", editable=True),
                "quality": ConfigField(value=90, editable=True),
            },
        ),
        NodeInstance(id="3", type="pipeline.output"),
    ],
    edges=[
        Edge(source="1", target="2"),
        Edge(source="2", target="3"),
    ],
)


async def main():
    ctx = create_context(b"\xff" * 1024, "heic")
    outputs = await run_pipeline(pipeline, registry, transport, ctx)
    for output in outputs:
        print(output.metadata.output_file_name, len(output.file))


asyncio.run(main())
```

## Core concepts

### Pipeline

A directed acyclic graph (DAG) of nodes connected by edges:

```python
@dataclass
class Pipeline:
    nodes: list[NodeInstance]
    edges: list[Edge]
```

Pipelines are plain data — serialise them to JSON, store them, share them, version them.

### Nodes

Each node is an atomic operation. Every node receives an `ExecutionContext` and returns one of:

- `continue` — pass the (possibly modified) context downstream
- `skip` — this branch doesn't apply; downstream nodes inherit the skip
- `output` — terminal result; collected as a pipeline output

Built-in nodes are grouped by media: **image**, **video**, and **audio** each have filter, convert, resize (where it applies), and `strip-metadata`. **Common** nodes are `pipeline.input` (entry) and `pipeline.output` (terminal — names the file and collects the result). Exact type strings and defaults live in `NODE_CATALOG` and `default_config_for_pipeline_node_type()` in code — no need to duplicate them here.

### Metadata stripping

Metadata handling is an explicit graph operation, not a flag on the output. Drop `image.strip-metadata`, `video.strip-metadata`, or `audio.strip-metadata` into the branch that should come out clean; leave other branches untouched to keep EXIF/XMP/IPTC/container tags. Each strip node has one boolean config field, `enabled` (default `True`) — set to `False` to bypass the node without removing it from the graph.

Transports implement the `operation: "strip-metadata"` payload as a lossless pass when possible (`ffmpeg -c copy -map_metadata -1` for video/audio; chunk-walk or re-emit without tag data for images). **ICC color profiles are always preserved** to avoid unintended color shifts.

Because stripping is a regular node, two `pipeline.output` nodes can share an upstream `image.convert` and differ only in whether a `strip-metadata` node sits before one of them — no per-output flag propagation, no conflict error.

For JPEG/PNG you can also call `strip_image_metadata_lossless(data, ext)` directly — a bytewise walker that removes EXIF/XMP/IPTC/tEXt chunks without re-encoding pixel data.

### Transport

The SDK never processes files directly. Nodes call `transport.convert()` and the host decides how:

```python
class Transport(Protocol):
    async def convert(self, file: bytes, config: dict[str, Any]) -> bytes: ...
    async def convert_from_path(self, path: str, config: dict[str, Any]) -> bytes: ...
```

This makes pipelines portable. The same pipeline works with any backend.

For tests and quick experiments without a real encoder, use `create_mock_transport()`.

### Config fields

Node configuration uses a structured format that supports both locked presets and user-editable values:

```python
@dataclass
class ConfigField:
    value: Any
    editable: bool
    options: Optional[Sequence[Any]] = None
```

## Validation

Validate a pipeline without executing it:

```python
from transformkit import create_default_registry, validate_pipeline

result = validate_pipeline(pipeline, create_default_registry())

if not result.valid:
    for err in result.errors:
        print(err.code, err.message)
    # NO_INPUT  "Pipeline must have at least one Input node."
```

Checks for: missing input/output nodes, duplicate IDs, dangling edges, unknown node types, cycles, disconnected nodes, and mixed media types (a pipeline must stay within a single `image.*` / `video.*` / `audio.*` family).

## Custom nodes

Register your own node types:

```python
from transformkit import NodeDefinition, create_default_registry

registry = create_default_registry()


async def watermark(ctx, config, transport):
    text = config["text"].value if "text" in config else "watermark"
    buffer = await transport.convert(
        ctx.file,
        {
            "operation": "watermark",
            "text": text,
            "inputExtension": ctx.metadata.extension,
        },
    )
    from transformkit import ExecutionContext, NodeResultContinue
    from copy import copy
    return NodeResultContinue(
        ctx=ExecutionContext(file=buffer, metadata=copy(ctx.metadata))
    )


registry.register(NodeDefinition(type="image.watermark", execute=watermark))
```

## Testing

The SDK exports a mock transport for tests:

```python
from transformkit import create_mock_transport

transport = create_mock_transport()  # returns input bytes unchanged
```

## API reference

### Engine

| Export                                                 | Description                                |
| ------------------------------------------------------ | ------------------------------------------ |
| `run_pipeline(pipeline, registry, transport, ctx)`     | Execute a pipeline, return output contexts |
| `process_files(files, pipeline, registry, transport)`  | Run a pipeline once per file               |
| `create_context(buffer, extension)`                    | Create an execution context from bytes     |
| `create_default_registry()`                            | Registry with all built-in nodes           |
| `validate_pipeline(pipeline, registry=None)`           | Structural validation without execution    |

### Client

| Export                  | Description                                     |
| ----------------------- | ----------------------------------------------- |
| `create_client(...)`    | File queue + processing (API or transport mode) |

### MIME utilities

| Export                                     | Description                      |
| ------------------------------------------ | -------------------------------- |
| `IMAGE_MIME` / `VIDEO_MIME` / `AUDIO_MIME` | Extension → MIME maps            |
| `mime_from_extension(ext)`                 | Look up MIME by extension        |
| `extension_from_mime(mime)`                | Reverse lookup                   |
| `accept_string(category)`                  | HTML `<input accept="…">` string |

### Pipeline defaults

| Export                                         | Description                                  |
| ---------------------------------------------- | -------------------------------------------- |
| `default_config_for_pipeline_node_type(type)`  | Default config for a node type               |
| `merge_pipeline_node_config(type, config)`     | Merge saved config onto defaults             |
| `NODE_CATALOG`                                 | Built-in node types + categories for pickers |

### Lossless image metadata stripping

| Export                                    | Description                                |
| ----------------------------------------- | ------------------------------------------ |
| `strip_image_metadata_lossless(data, ext)` | Walk JPEG/PNG bytes and drop metadata      |
| `is_strip_supported_extension(ext)`       | True for `jpg`, `jpeg`, `png`              |

## License

MIT
