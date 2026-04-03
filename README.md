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
        NodeInstance(id="out", type="output.console"),
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

## License

MIT
