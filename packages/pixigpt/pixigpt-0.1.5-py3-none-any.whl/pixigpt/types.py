"""Type definitions for PixiGPT API."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ToolCallFunction:
    """Function details within a tool call."""
    name: str
    arguments: str  # JSON string


@dataclass
class ToolCall:
    """Tool call made by the assistant."""
    id: str
    type: str
    function: ToolCallFunction


@dataclass
class Message:
    """Chat message."""
    role: str
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None  # For role="tool" messages


@dataclass
class ChatCompletionRequest:
    """Request for chat completion.

    assistant_id is optional - if omitted, messages[0] must be a system message.
    tools can be provided to override assistant's configured tools.
    """
    messages: List[Message]
    assistant_id: Optional[str] = None
    temperature: float = 0.0  # Server defaults to 0.6 if 0
    max_tokens: int = 0       # Server omits if 0 (vLLM default)
    enable_thinking: Optional[bool] = None
    tools: Optional[List[Dict[str, Any]]] = None  # OpenAI-format tool definitions


@dataclass
class Usage:
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatCompletionChoice:
    """Chat completion choice."""
    index: int
    message: Message
    finish_reason: str
    reasoning_content: Optional[str] = None  # Chain of thought reasoning


@dataclass
class ChatCompletionResponse:
    """Response from chat completion."""
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage


@dataclass
class Thread:
    """Conversation thread."""
    id: str
    object: str
    created_at: int
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class MessageContent:
    """Message content block."""
    type: str
    text: Dict[str, Any]


@dataclass
class MessageSource:
    """Source attachment from tools like WebSearch, Fetch."""
    id: str
    tool_name: str
    title: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None


@dataclass
class MessageMedia:
    """Media attachment from DrawImage, EditImage, UserUpload."""
    id: str  # ShortID
    source: str
    type: str  # image, audio
    signed_url: str  # 24h temporary R2 signed URL
    prompt: Optional[str] = None
    description: Optional[str] = None


@dataclass
class MessageCode:
    """Code execution result."""
    id: str
    language: str
    code: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    execution_time_ms: Optional[int] = None


@dataclass
class ThreadMessage:
    """Message in a thread."""
    id: str
    object: str
    created_at: int
    thread_id: str
    role: str
    content: List[MessageContent]
    reasoning_content: Optional[str] = None  # Chain of thought reasoning
    # Attachments from tool execution (Pixi tools only)
    sources: Optional[List[MessageSource]] = None
    media: Optional[List[MessageMedia]] = None
    code: Optional[List[MessageCode]] = None


@dataclass
class Run:
    """Async run."""
    id: str
    object: str
    created_at: int
    thread_id: str
    assistant_id: str
    status: str  # queued, in_progress, completed, failed
    model: str
    message: Optional[ThreadMessage] = None  # Populated when completed


@dataclass
class Assistant:
    """AI assistant."""
    id: str
    object: str
    created_at: int
    name: str
    instructions: str
    tools_config: Optional[str] = None


@dataclass
class VisionUsage:
    """Token usage for vision API calls."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class VisionAnalyzeRequest:
    """Request to analyze an image."""
    image_url: str
    user_prompt: Optional[str] = None


@dataclass
class VisionAnalyzeResponse:
    """Response from image analysis."""
    result: str
    usage: VisionUsage


@dataclass
class VisionTagsRequest:
    """Request to generate tags for an image."""
    image_url: str


@dataclass
class VisionTagsResponse:
    """Response from tag generation."""
    result: str
    usage: VisionUsage


@dataclass
class VisionOCRRequest:
    """Request to extract text from an image."""
    image_url: str


@dataclass
class VisionOCRResponse:
    """Response from OCR."""
    result: str
    usage: VisionUsage


@dataclass
class VisionVideoRequest:
    """Request to analyze a video."""
    video_url: str
    user_prompt: Optional[str] = None


@dataclass
class VisionVideoResponse:
    """Response from video analysis."""
    result: str
    usage: VisionUsage


@dataclass
class ModerationTextRequest:
    """Request to moderate text."""
    prompt: str


@dataclass
class ModerationMediaRequest:
    """Request to moderate image/video."""
    media_url: str
    is_video: bool


@dataclass
class ModerationResponse:
    """Response from moderation."""
    category: str
    score: float
    usage: VisionUsage
