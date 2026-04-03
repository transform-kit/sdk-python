"""
transformkit — Node-based media pipeline engine for Python.
"""

from .client.client import create_client
from .client.types import (
    AddFileInput,
    AfterProcessFileHook,
    ClearFilesOptions,
    ClientOptionsApi,
    ClientOptionsTransport,
    ClientState,
    FileStatus,
    MediaType,
    OutputMetadata,
    OutputResult,
    PngCompressionSpeed,
    QueuedFile,
    TransformClient,
)
from .engine.context import create_context
from .engine.registry import NodeRegistry
from .engine.run_pipeline import process_files, run_pipeline
from .engine.validate import ValidationError, ValidationResult, validate_pipeline
from .mime import (
    AUDIO_MIME,
    IMAGE_MIME,
    VIDEO_MIME,
    accept_string,
    extension_from_mime,
    mime_from_extension,
)
from .nodes import create_default_registry
from .nodes.audio_convert.utils import BITRATE_OPTIONS as AUDIO_BITRATE_OPTIONS
from .nodes.image_convert.utils import (
    DEFAULT_PNG_COMPRESSION_SPEED,
    PNG_COMPRESSION_SPEED_OPTIONS,
    parse_png_compression_speed,
)
from .nodes.output_console.utils import DEFAULT_NAME_SUFFIX_FIELD
from .pipeline_node_defaults import (
    NODE_CATALOG,
    default_config_for_pipeline_node_type,
    merge_pipeline_node_config,
)
from .transport.mock import create_mock_transport
from .types import (
    ConfigField,
    Edge,
    ExecutionContext,
    Metadata,
    NodeCatalogEntry,
    NodeDefinition,
    NodeInstance,
    NodeResult,
    NodeResultContinue,
    NodeResultOutput,
    NodeResultSkip,
    Pipeline,
    Transport,
)
from .utils import is_editable, normalize_ext

__version__ = "0.1.0"

__all__ = [
    # Types
    "ConfigField",
    "Edge",
    "ExecutionContext",
    "Metadata",
    "NodeCatalogEntry",
    "NodeDefinition",
    "NodeInstance",
    "NodeResult",
    "NodeResultContinue",
    "NodeResultOutput",
    "NodeResultSkip",
    "Pipeline",
    "PngCompressionSpeed",
    "Transport",
    # MIME
    "IMAGE_MIME",
    "VIDEO_MIME",
    "AUDIO_MIME",
    "mime_from_extension",
    "extension_from_mime",
    "accept_string",
    # Node utils
    "AUDIO_BITRATE_OPTIONS",
    "DEFAULT_PNG_COMPRESSION_SPEED",
    "PNG_COMPRESSION_SPEED_OPTIONS",
    "parse_png_compression_speed",
    "DEFAULT_NAME_SUFFIX_FIELD",
    # Pipeline defaults
    "NODE_CATALOG",
    "default_config_for_pipeline_node_type",
    "merge_pipeline_node_config",
    # Registry
    "NodeRegistry",
    # Engine
    "run_pipeline",
    "process_files",
    # Validation
    "ValidationError",
    "ValidationResult",
    "validate_pipeline",
    # Nodes
    "create_default_registry",
    # Context
    "create_context",
    # Transport
    "create_mock_transport",
    # Client
    "create_client",
    "AddFileInput",
    "AfterProcessFileHook",
    "ClearFilesOptions",
    "ClientOptionsApi",
    "ClientOptionsTransport",
    "ClientState",
    "FileStatus",
    "MediaType",
    "OutputMetadata",
    "OutputResult",
    "QueuedFile",
    "TransformClient",
    # Utils
    "is_editable",
    "normalize_ext",
]
