
__version__ = "0.0.41"

from .client import GravixLayer
from .types.async_client import AsyncGravixLayer
from .types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionChoice,
    ChatCompletionUsage,
    FunctionCall,
    ToolCall,
)
from .types.embeddings import (
    EmbeddingResponse,
    EmbeddingObject,
    EmbeddingUsage,
)
from .types.completions import (
    Completion,
    CompletionChoice,
    CompletionUsage,
)
from .types.deployments import (
    DeploymentCreate,
    Deployment,
    DeploymentList,
    DeploymentResponse,
)
from .types.files import (
    FileObject,
    FileUploadResponse,
    FileListResponse,
    FileDeleteResponse,
    FILE_PURPOSES,
)
from .types.vectors import (
    VectorIndex,
    VectorIndexList,
    Vector,
    TextVector,
    VectorSearchResponse,
    TextSearchResponse,
    BatchUpsertResponse,
    VectorListResponse,
    VectorDictResponse,
    VectorSearchHit,
    SUPPORTED_METRICS,
    SUPPORTED_VECTOR_TYPES,
)
from .types.sandbox import (
    Sandbox,
    SandboxList,
    SandboxMetrics,
    SandboxTimeoutResponse,
    SandboxHostURL,
    FileReadResponse,
    FileWriteResponse,
    FileListResponse,
    FileInfo,
    FileDeleteResponse,
    DirectoryCreateResponse,
    FileUploadResponse,
    CommandRunResponse,
    CodeRunResponse,
    CodeContext,
    CodeContextDeleteResponse,
    Template,
    TemplateList,
    SandboxKillResponse,
)
# Memory imports will be done lazily to avoid circular imports

__all__ = [
    "GravixLayer",
    "AsyncGravixLayer",
    "ChatCompletion",
    "ChatCompletionMessage",
    "ChatCompletionChoice",
    "ChatCompletionUsage",
    "FunctionCall",
    "ToolCall",
    "EmbeddingResponse",
    "EmbeddingObject",
    "EmbeddingUsage",
    "Completion",
    "CompletionChoice",
    "CompletionUsage",
    "DeploymentCreate",
    "Deployment",
    "DeploymentList",
    "DeploymentResponse",
    "FileObject",
    "FileUploadResponse",
    "FileListResponse",
    "FileDeleteResponse",
    "FILE_PURPOSES",
    "VectorIndex",
    "VectorIndexList",
    "Vector",
    "TextVector",
    "VectorSearchResponse",
    "TextSearchResponse",
    "BatchUpsertResponse",
    "VectorListResponse",
    "VectorDictResponse",
    "VectorSearchHit",
    "SUPPORTED_METRICS",
    "SUPPORTED_VECTOR_TYPES",
    # Sandbox types
    "Sandbox",
    "SandboxList",
    "SandboxMetrics",
    "SandboxTimeoutResponse",
    "SandboxHostURL",
    "FileReadResponse",
    "FileWriteResponse",
    "FileListResponse",
    "FileInfo",
    "FileDeleteResponse",
    "DirectoryCreateResponse",
    "FileUploadResponse",
    "CommandRunResponse",
    "CodeRunResponse",
    "CodeContext",
    "CodeContextDeleteResponse",
    "Template",
    "TemplateList",
    "SandboxKillResponse",
    # Memory types
    "Memory",
    "MemoryType",
    "MemoryEntry",
    "MemorySearchResult",
    "MemoryStats",
]

# Import memory classes directly to make them visible in dir()
try:
    from .resources.memory import Memory, MemoryType, MemoryEntry, MemorySearchResult, MemoryStats
except ImportError:
    # Fallback to lazy imports if there are circular dependency issues
    def __getattr__(name):
        if name == "Memory":
            from .resources.memory import Memory
            return Memory
        elif name == "MemoryType":
            from .resources.memory import MemoryType
            return MemoryType
        elif name == "MemoryEntry":
            from .resources.memory import MemoryEntry
            return MemoryEntry
        elif name == "MemorySearchResult":
            from .resources.memory import MemorySearchResult
            return MemorySearchResult
        elif name == "MemoryStats":
            from .resources.memory import MemoryStats
            return MemoryStats
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
