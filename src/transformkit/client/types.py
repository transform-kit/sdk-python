"""Client types mirroring the TypeScript SDK client."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional, Protocol, Union

MediaType = Literal["image", "video", "audio"]
FileStatus = Literal["unprocessed", "in_progress", "processed", "skipped", "error"]

PngCompressionSpeed = Literal["fast", "medium", "slow"]


@dataclass
class OutputResult:
    """Output from pipeline execution."""

    file: bytes
    metadata: "OutputMetadata"


@dataclass
class OutputMetadata:
    extension: str
    mime_type: str
    output_file_name: Optional[str] = None
    overwrite_source: Optional[bool] = None


@dataclass
class AddFileInput:
    """Input when adding files to the client queue."""

    name: str
    size: int
    type: str
    id: Optional[str] = None
    file_bytes: Optional[bytes] = None
    path: Optional[str] = None


@dataclass
class QueuedFile:
    """Queued file with derived media_type, status, and optional outputs."""

    id: str
    name: str
    size: int
    type: str
    media_type: MediaType
    status: FileStatus = "unprocessed"
    file_bytes: Optional[bytes] = None
    path: Optional[str] = None
    outputs: Optional[list[OutputResult]] = None


@dataclass
class ClientState:
    """Snapshot of the client's file queue and processing status."""

    files: list[QueuedFile] = field(default_factory=list)
    is_processing: bool = False


@dataclass
class ClearFilesOptions:
    """Options for :meth:`TransformClient.clear_files`."""

    status: Union[Literal["all"], FileStatus] = "all"


@dataclass
class ClientOptionsApi:
    """Client options for API mode (pipeline runs server-side via HTTP)."""

    api_key: Optional[str] = None
    base_url: str = "http://localhost:3002"
    read_file: Optional[Callable[..., Any]] = None
    after_process_file: Optional["AfterProcessFileHook"] = None


@dataclass
class ClientOptionsTransport:
    """Client options for local/transport mode (pipeline runs in-process)."""

    transport: Any
    read_file: Optional[Callable[..., Any]] = None
    after_process_file: Optional["AfterProcessFileHook"] = None


ClientOptions = Union[ClientOptionsApi, ClientOptionsTransport]

AfterProcessFileHook = Callable[["QueuedFile", list["OutputResult"]], Any]


class TransformClient(Protocol):
    """Public interface returned by ``create_client``."""

    def add_files(self, inputs: list[AddFileInput]) -> None: ...
    def remove_file(self, id_: str) -> None: ...
    def clear_files(self, media_type: Optional[MediaType] = None, *, status: str = "all") -> None: ...
    def requeue_after_pipeline_change(self, media_type: MediaType) -> None: ...
    async def process(self, pipeline: Any, media_type: Optional[MediaType] = None) -> None: ...
    def get_state(self) -> ClientState: ...
    def subscribe(self, listener: Callable[[ClientState], None]) -> Callable[[], None]: ...
