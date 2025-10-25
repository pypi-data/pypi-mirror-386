"""PixiGPT Python Client - Production-grade API client."""

from .client import Client
from .types import (
    Message,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Thread,
    ThreadMessage,
    Run,
    Assistant,
    VisionAnalyzeRequest,
    VisionAnalyzeResponse,
    VisionTagsRequest,
    VisionTagsResponse,
    VisionOCRRequest,
    VisionOCRResponse,
    VisionVideoRequest,
    VisionVideoResponse,
    ModerationTextRequest,
    ModerationMediaRequest,
    ModerationResponse,
)
from .errors import APIError, is_auth_error, is_rate_limit_error

__version__ = "0.1.0"
__all__ = [
    "Client",
    "Message",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "Thread",
    "ThreadMessage",
    "Run",
    "Assistant",
    "VisionAnalyzeRequest",
    "VisionAnalyzeResponse",
    "VisionTagsRequest",
    "VisionTagsResponse",
    "VisionOCRRequest",
    "VisionOCRResponse",
    "VisionVideoRequest",
    "VisionVideoResponse",
    "ModerationTextRequest",
    "ModerationMediaRequest",
    "ModerationResponse",
    "APIError",
    "is_auth_error",
    "is_rate_limit_error",
]
