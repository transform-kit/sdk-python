"""In-memory file processing client with queue, state, and hooks.

Supports two modes:
- **Transport mode** — runs the pipeline in-process using the provided Transport.
- **API mode** — sends files to a remote pipeline endpoint via HTTP.
"""

from __future__ import annotations

import json
import logging
from copy import copy
from typing import Any, Callable, Optional, Union
from urllib.request import Request, urlopen

from ..engine.context import create_context
from ..mime import AUDIO_MIME, IMAGE_MIME, VIDEO_MIME, extension_from_mime
from ..nodes import create_default_registry
from ..engine.run_pipeline import run_pipeline
from ..transport.api import resolve_pipeline_url
from ..types import Pipeline, Transport
from ..utils import next_tick
from .types import (
    AddFileInput,
    AfterProcessFileHook,
    ClientOptionsApi,
    ClientOptionsTransport,
    ClientState,
    FileStatus,
    MediaType,
    OutputMetadata,
    OutputResult,
    QueuedFile,
)

logger = logging.getLogger("transformkit")


def _get_media_type(input_: AddFileInput) -> Optional[MediaType]:
    t = (input_.type or "").lower()
    if t.startswith("image/"):
        return "image"
    if t.startswith("video/"):
        return "video"
    if t.startswith("audio/"):
        return "audio"
    ext = input_.name.rsplit(".", 1)[-1].lower()
    if ext in IMAGE_MIME:
        return "image"
    if ext in VIDEO_MIME:
        return "video"
    if ext in AUDIO_MIME:
        return "audio"
    return None


def _ext_from_name(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower()


def _build_multipart(file_bytes: bytes, file_name: str, pipeline: Pipeline) -> tuple[bytes, str]:
    """Build a multipart/form-data body with file + pipeline JSON."""
    import os
    boundary = f"----TransformKit{os.urandom(16).hex()}"
    parts: list[bytes] = []

    parts.append(f"--{boundary}\r\n".encode())
    parts.append(f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'.encode())
    parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
    parts.append(file_bytes)
    parts.append(b"\r\n")

    def _serialize_config_field(f: Any) -> dict[str, Any]:
        d: dict[str, Any] = {"value": f.value, "editable": f.editable}
        if getattr(f, "options", None) is not None:
            d["options"] = f.options
        return d

    pipeline_json = json.dumps({
        "nodes": [
            {
                "id": n.id,
                "type": n.type,
                **({"config": {k: _serialize_config_field(v) for k, v in n.config.items()}} if n.config else {}),
            }
            for n in pipeline.nodes
        ],
        "edges": [{"source": e.source, "target": e.target} for e in pipeline.edges],
    })
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(b'Content-Disposition: form-data; name="pipeline"\r\n')
    parts.append(b"Content-Type: application/json\r\n\r\n")
    parts.append(pipeline_json.encode())
    parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode())
    content_type = f"multipart/form-data; boundary={boundary}"
    return b"".join(parts), content_type


def _output_name_and_extension_from_headers(
    headers: dict[str, str],
    mime_type: str,
) -> tuple[Optional[str], str]:
    """Extract the output filename and extension from HTTP response headers."""
    import urllib.parse

    xf = headers.get("x-transform-output-filename", "")
    if xf:
        try:
            decoded = urllib.parse.unquote(xf.strip())
            base = decoded.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].strip()
            if base:
                dot = base.rfind(".")
                extension = base[dot + 1:].lower() if dot > 0 else extension_from_mime(mime_type)
                return base, extension
        except Exception:
            pass

    cd = headers.get("content-disposition", "")
    if cd:
        import re
        utf8 = re.search(r"filename\*=UTF-8''([^;\s]+)", cd, re.IGNORECASE)
        if utf8:
            try:
                base = urllib.parse.unquote(utf8.group(1).strip("'\"")).rsplit("/", 1)[-1].rsplit("\\", 1)[-1].strip()
                if base:
                    dot = base.rfind(".")
                    extension = base[dot + 1:].lower() if dot > 0 else extension_from_mime(mime_type)
                    return base, extension
            except Exception:
                pass
        quoted = re.search(r'filename="([^"]+)"', cd, re.IGNORECASE)
        unquoted = quoted or re.search(r"filename=([^;\s]+)", cd, re.IGNORECASE)
        if unquoted:
            base = unquoted.group(1).strip("'\"").rsplit("/", 1)[-1].rsplit("\\", 1)[-1].strip()
            if base:
                dot = base.rfind(".")
                extension = base[dot + 1:].lower() if dot > 0 else extension_from_mime(mime_type)
                return base, extension

    return None, extension_from_mime(mime_type)


async def _run_pipeline_via_http(
    pipeline_url: str,
    api_key: Optional[str],
    file: QueuedFile,
    pipeline: Pipeline,
    read_bytes: Callable[[QueuedFile], Any],
) -> tuple[bool, list[OutputResult]]:
    """Execute a pipeline via the remote HTTP API endpoint."""
    if file.file_bytes:
        raw_bytes = file.file_bytes
    else:
        raw_bytes = await read_bytes(file)

    body, content_type = _build_multipart(raw_bytes, file.name, pipeline)

    headers_dict: dict[str, str] = {"Content-Type": content_type}
    if api_key:
        headers_dict["Authorization"] = f"Bearer {api_key}"

    req = Request(pipeline_url, data=body, headers=headers_dict, method="POST")

    import asyncio
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: urlopen(req))

    status_code = response.status
    resp_headers = {k.lower(): v for k, v in response.getheaders()}
    resp_body = response.read()

    if status_code < 200 or status_code >= 300:
        raise RuntimeError(f"API pipeline failed ({status_code}): {resp_body.decode(errors='replace')}")

    ct = resp_headers.get("content-type", "")
    if "application/json" in ct:
        j = json.loads(resp_body)
        if isinstance(j, dict) and j.get("skipped") is True:
            return True, []
        raise RuntimeError("Unexpected JSON response from pipeline API")

    mime_type = ct or "application/octet-stream"
    output_file_name, extension = _output_name_and_extension_from_headers(resp_headers, mime_type)

    return False, [OutputResult(
        file=resp_body,
        metadata=OutputMetadata(
            extension=extension,
            mime_type=mime_type,
            output_file_name=output_file_name,
            overwrite_source=False,
        ),
    )]


class _Client:
    """Concrete client implementation supporting both transport and API modes."""

    def __init__(
        self,
        options: Union[ClientOptionsApi, ClientOptionsTransport],
    ) -> None:
        self._options = options
        self._is_api = isinstance(options, ClientOptionsApi)
        self._after_process_file = options.after_process_file
        self._read_file = options.read_file
        self._state = ClientState()
        self._listeners: set[Callable[[ClientState], None]] = set()

    def _notify(self) -> None:
        s = ClientState(files=list(self._state.files), is_processing=self._state.is_processing)
        for fn in self._listeners:
            fn(s)

    def _set_state(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self._state, k, v)
        self._notify()

    def _set_file_result(self, id_: str, status: FileStatus, outputs: Optional[list[OutputResult]] = None) -> None:
        new_files = []
        for f in self._state.files:
            if f.id == id_:
                f = copy(f)
                f.status = status
                if outputs is not None:
                    f.outputs = outputs
            new_files.append(f)
        self._state.files = new_files
        self._notify()

    def add_files(self, inputs: list[AddFileInput]) -> None:
        ids = {f.id for f in self._state.files}
        added: list[QueuedFile] = []
        for inp in inputs:
            media_type = _get_media_type(inp)
            if media_type is None:
                continue
            id_ = inp.id or (inp.path if inp.path else f"{inp.name}-{inp.size}")
            if id_ in ids:
                continue
            ids.add(id_)
            added.append(QueuedFile(
                id=id_,
                name=inp.name,
                size=inp.size,
                type=inp.type,
                media_type=media_type,
                file_bytes=inp.file_bytes,
                path=inp.path,
            ))
        if added:
            self._set_state(files=[*self._state.files, *added])

    def remove_file(self, id_: str) -> None:
        self._set_state(files=[f for f in self._state.files if f.id != id_])

    def clear_files(self, media_type: Optional[MediaType] = None, *, status: str = "all") -> None:
        if media_type is None:
            self._set_state(files=[])
            return
        if status == "all":
            self._set_state(files=[f for f in self._state.files if f.media_type != media_type])
        else:
            self._set_state(files=[
                f for f in self._state.files if not (f.media_type == media_type and f.status == status)
            ])

    def requeue_after_pipeline_change(self, media_type: MediaType) -> None:
        new_files = []
        for f in self._state.files:
            if f.media_type == media_type and f.status in ("processed", "skipped"):
                f = copy(f)
                f.status = "unprocessed"
                f.outputs = None
            new_files.append(f)
        self._state.files = new_files
        self._notify()

    async def _get_file_bytes(self, file: QueuedFile) -> bytes:
        if file.file_bytes:
            return file.file_bytes
        if file.path and self._read_file:
            return await self._read_file(path=file.path)
        raise RuntimeError("Cannot read file: need file_bytes or path + read_file")

    async def process(self, pipeline: Pipeline, media_type: Optional[MediaType] = None) -> None:
        if self._state.is_processing:
            return

        pending = [
            f for f in self._state.files
            if f.status in ("unprocessed", "error") and (media_type is None or f.media_type == media_type)
        ]
        if not pending:
            return

        use_http = self._is_api
        registry = None if use_http else create_default_registry()
        transport: Optional[Transport] = None if use_http else getattr(self._options, "transport", None)

        api_opts = self._options if use_http else None
        pipeline_url = ""
        api_key: Optional[str] = None
        if isinstance(api_opts, ClientOptionsApi):
            pipeline_url = resolve_pipeline_url(api_opts.base_url)
            api_key = api_opts.api_key

        self._set_state(is_processing=True)

        try:
            for file in pending:
                self._set_file_result(file.id, "in_progress")
                await next_tick()

                try:
                    if use_http:
                        skipped, output_results = await _run_pipeline_via_http(
                            pipeline_url, api_key, file, pipeline, self._get_file_bytes,
                        )
                        done_status: FileStatus = "skipped" if skipped else "processed"
                        if self._after_process_file and output_results:
                            result = self._after_process_file(file, output_results)
                            if hasattr(result, "__await__"):
                                await result
                        self._set_file_result(file.id, done_status, output_results)
                    else:
                        assert transport is not None
                        assert registry is not None
                        ext = _ext_from_name(file.name)

                        if file.path and callable(getattr(transport, "convert_from_path", None)):
                            ctx = create_context(b"", ext)
                            ctx.metadata.source_path = file.path
                        else:
                            raw = await self._get_file_bytes(file)
                            ctx = create_context(raw, ext)

                        ctx.metadata.source_file_name = file.name
                        outputs = await run_pipeline(pipeline, registry, transport, ctx)
                        done_status = "processed" if outputs else "skipped"
                        output_results = [
                            OutputResult(
                                file=o.file,
                                metadata=OutputMetadata(
                                    extension=o.metadata.extension,
                                    mime_type=o.metadata.mime_type,
                                    output_file_name=o.metadata.output_file_name,
                                    overwrite_source=o.metadata.overwrite_source,
                                ),
                            )
                            for o in outputs
                        ]
                        if self._after_process_file and output_results:
                            result = self._after_process_file(file, output_results)
                            if hasattr(result, "__await__"):
                                await result
                        self._set_file_result(file.id, done_status, output_results)
                except Exception as err:
                    logger.error("[transformkit] process failed %s: %s", file.name, err)
                    self._set_file_result(file.id, "error")
        finally:
            self._set_state(is_processing=False)

    def get_state(self) -> ClientState:
        return ClientState(files=list(self._state.files), is_processing=self._state.is_processing)

    def subscribe(self, listener: Callable[[ClientState], None]) -> Callable[[], None]:
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)


def create_client(
    options: Union[ClientOptionsApi, ClientOptionsTransport, None] = None,
    *,
    transport: Optional[Transport] = None,
    api_key: Optional[str] = None,
    base_url: str = "http://localhost:3002",
    read_file: Optional[Callable[..., Any]] = None,
    after_process_file: Optional[AfterProcessFileHook] = None,
) -> _Client:
    """Create a file processing client with an in-memory queue.

    Supports two modes:

    **Transport mode** — runs the pipeline in-process::

        client = create_client(transport=my_transport)

    **API mode** — sends files to a remote pipeline endpoint via HTTP::

        client = create_client(api_key="sk-...", base_url="https://api.transform-kit.com")

    You can also pass a :class:`ClientOptionsApi` or :class:`ClientOptionsTransport`
    dataclass as the first argument.
    """
    if options is not None:
        return _Client(options)

    if transport is not None:
        return _Client(ClientOptionsTransport(
            transport=transport,
            read_file=read_file,
            after_process_file=after_process_file,
        ))

    return _Client(ClientOptionsApi(
        api_key=api_key,
        base_url=base_url,
        read_file=read_file,
        after_process_file=after_process_file,
    ))
