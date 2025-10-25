"""PixiGPT API client with production-grade HTTP handling."""

import time
import re
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .types import (
    Message,
    ToolCall,
    ToolCallFunction,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    Usage,
    Thread,
    ThreadMessage,
    MessageContent,
    MessageSource,
    MessageMedia,
    MessageCode,
    Run,
    Assistant,
    VisionUsage,
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
from .errors import APIError


class Client:
    """
    PixiGPT API client with production-grade defaults.

    Features:
    - Connection pooling (100 connections)
    - Smart retries with exponential backoff
    - 30s timeout
    - Keep-alive enabled
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        session: Optional[requests.Session] = None,
    ):
        """
        Create a new PixiGPT client.

        Args:
            api_key: PixiGPT API key
            base_url: Base URL for API (e.g., https://pixigpt.com/v1)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
            session: Custom requests.Session (optional)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        if session:
            self.session = session
        else:
            # Create session with connection pooling and retries
            self.session = requests.Session()

            # Connection pooling
            adapter = HTTPAdapter(
                pool_connections=100,
                pool_maxsize=100,
                max_retries=Retry(
                    total=max_retries,
                    backoff_factor=0.1,  # 0.1s, 0.2s, 0.4s, 0.8s...
                    status_forcelist=[500, 502, 503, 504],  # Retry on server errors
                    allowed_methods=["GET", "POST", "PUT", "DELETE"],
                ),
            )
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)

            # Default headers
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )

    def _request(self, method: str, path: str, json: Optional[dict] = None) -> dict:
        """Execute HTTP request with error handling."""
        url = urljoin(self.base_url + "/", path.lstrip("/"))

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json,
                timeout=self.timeout,
            )

            # Handle HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json().get("error", {})
                except Exception:
                    error_data = {"message": response.text, "type": "unknown"}

                raise APIError(error_data, response.status_code)

            return response.json() if response.text else {}

        except requests.RequestException as e:
            raise APIError(
                {"message": str(e), "type": "request_error"}, 0
            ) from e

    @staticmethod
    def _extract_reasoning(content: str) -> Tuple[str, Optional[str]]:
        """
        Extract chain of thought reasoning from content.

        Returns:
            (main_content, reasoning_content)
        """
        # Match <think>...</think> or <thinking>...</thinking>
        think_pattern = r"<think(?:ing)?>(.*?)</think(?:ing)?>"
        match = re.search(think_pattern, content, re.DOTALL | re.IGNORECASE)

        if match:
            reasoning = match.group(1).strip()
            # Remove thinking tags from main content
            main_content = re.sub(think_pattern, "", content, flags=re.DOTALL | re.IGNORECASE).strip()
            return main_content, reasoning

        return content, None

    def create_chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """
        Create a stateless chat completion.

        Example:
            >>> client = Client(api_key, base_url)
            >>> response = client.create_chat_completion(
            ...     ChatCompletionRequest(
            ...         messages=[
            ...             Message(role="system", content="You are helpful"),
            ...             Message(role="user", content="Hello!")
            ...         ],
            ...         assistant_id="...",  # Optional
            ...     )
            ... )
            >>> print(response.choices[0].message.content)
        """
        # Build messages with tool support
        messages = []
        for m in request.messages:
            msg_dict = {"role": m.role, "content": m.content}
            if m.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in m.tool_calls
                ]
            if m.tool_call_id:
                msg_dict["tool_call_id"] = m.tool_call_id
            messages.append(msg_dict)

        data = {"messages": messages}

        # Optional fields
        if request.assistant_id:
            data["assistant_id"] = request.assistant_id
        if request.temperature > 0:
            data["temperature"] = request.temperature
        if request.max_tokens > 0:
            data["max_tokens"] = request.max_tokens
        if request.enable_thinking is not None:
            data["enable_thinking"] = request.enable_thinking
        if request.tools:
            data["tools"] = request.tools

        resp = self._request("POST", "/chat/completions", json=data)

        # Parse response (server now provides reasoning_content directly)
        choices = []
        for choice_data in resp["choices"]:
            msg_data = choice_data["message"]

            # Parse tool calls if present
            tool_calls = None
            if "tool_calls" in msg_data and msg_data["tool_calls"]:
                tool_calls = [
                    ToolCall(
                        id=tc["id"],
                        type=tc["type"],
                        function=ToolCallFunction(
                            name=tc["function"]["name"],
                            arguments=tc["function"]["arguments"],
                        ),
                    )
                    for tc in msg_data["tool_calls"]
                ]

            choices.append(
                ChatCompletionChoice(
                    index=choice_data["index"],
                    message=Message(
                        role=msg_data["role"],
                        content=msg_data["content"],
                        tool_calls=tool_calls,
                    ),
                    finish_reason=choice_data["finish_reason"],
                    reasoning_content=choice_data.get("reasoning_content"),
                )
            )

        return ChatCompletionResponse(
            id=resp["id"],
            object=resp["object"],
            created=resp["created"],
            model=resp["model"],
            choices=choices,
            usage=Usage(**resp["usage"]),
        )

    def create_thread(self) -> Thread:
        """Create a new conversation thread."""
        resp = self._request("POST", "/threads", json={})
        return Thread(**resp)

    def get_thread(self, thread_id: str) -> Thread:
        """Retrieve a thread by ID."""
        resp = self._request("GET", f"/threads/{thread_id}")
        return Thread(**resp)

    def list_threads(self) -> List[Thread]:
        """List all API threads for the authenticated user."""
        resp = self._request("GET", "/threads")
        return [Thread(**t) for t in resp["data"]]

    def delete_thread(self, thread_id: str) -> None:
        """Delete a thread and all its messages."""
        self._request("DELETE", f"/threads/{thread_id}")

    def create_message(self, thread_id: str, role: str, content: str) -> ThreadMessage:
        """Add a message to a thread."""
        resp = self._request(
            "POST",
            f"/threads/{thread_id}/messages",
            json={"role": role, "content": content},
        )

        # Extract reasoning if present
        reasoning_content = None
        if resp.get("content") and len(resp["content"]) > 0:
            text_value = resp["content"][0].get("text", {}).get("value", "")
            _, reasoning_content = self._extract_reasoning(text_value)

        return ThreadMessage(
            id=resp["id"],
            object=resp["object"],
            created_at=resp["created_at"],
            thread_id=resp["thread_id"],
            role=resp["role"],
            content=[MessageContent(**c) for c in resp["content"]],
            reasoning_content=reasoning_content,
        )

    def create_messages_bulk(
        self, thread_id: str, messages: List[dict]
    ) -> List[ThreadMessage]:
        """
        Add multiple messages to a thread in one request.

        Args:
            thread_id: Thread ID
            messages: List of dicts with 'role' and 'content' keys

        Example:
            >>> messages = [
            ...     {"role": "user", "content": "Message 1"},
            ...     {"role": "user", "content": "Message 2"},
            ... ]
            >>> client.create_messages_bulk(thread_id, messages)
        """
        resp = self._request(
            "POST",
            f"/threads/{thread_id}/messages/bulk",
            json={"messages": messages},
        )

        result = []
        for msg_data in resp["data"]:
            # Extract reasoning if present
            reasoning_content = None
            if msg_data.get("content") and len(msg_data["content"]) > 0:
                text_value = msg_data["content"][0].get("text", {}).get("value", "")
                _, reasoning_content = self._extract_reasoning(text_value)

            result.append(
                ThreadMessage(
                    id=msg_data["id"],
                    object=msg_data["object"],
                    created_at=msg_data["created_at"],
                    thread_id=msg_data["thread_id"],
                    role=msg_data["role"],
                    content=[MessageContent(**c) for c in msg_data["content"]],
                    reasoning_content=reasoning_content,
                )
            )

        return result

    def list_messages(self, thread_id: str, limit: int = 20) -> List[ThreadMessage]:
        """List messages from a thread."""
        resp = self._request("GET", f"/threads/{thread_id}/messages?limit={limit}")

        messages = []
        for msg_data in resp["data"]:
            # Extract reasoning if present
            reasoning_content = None
            if msg_data.get("content") and len(msg_data["content"]) > 0:
                text_value = msg_data["content"][0].get("text", {}).get("value", "")
                _, reasoning_content = self._extract_reasoning(text_value)

            messages.append(
                ThreadMessage(
                    id=msg_data["id"],
                    object=msg_data["object"],
                    created_at=msg_data["created_at"],
                    thread_id=msg_data["thread_id"],
                    role=msg_data["role"],
                    content=[MessageContent(**c) for c in msg_data["content"]],
                    reasoning_content=reasoning_content,
                )
            )

        return messages

    def create_run(
        self,
        thread_id: str,
        assistant_id: str,
        temperature: float = 0.0,
        max_tokens: int = 0,
        enable_thinking: bool = True,
    ) -> Run:
        """
        Create an async run.

        Args:
            thread_id: Thread ID
            assistant_id: Assistant ID
            temperature: Temperature (0 = server default of 0.6)
            max_tokens: Max tokens (0 = vLLM default)
            enable_thinking: Enable chain of thought (default: True)
        """
        data = {
            "assistant_id": assistant_id,
            "enable_thinking": enable_thinking,
        }

        # Only include if > 0 (server handles defaults)
        if temperature > 0:
            data["temperature"] = temperature
        if max_tokens > 0:
            data["max_tokens"] = max_tokens

        resp = self._request("POST", f"/threads/{thread_id}/runs", json=data)
        return Run(**resp)

    def get_run(self, thread_id: str, run_id: str) -> Run:
        """Get run status."""
        resp = self._request("GET", f"/threads/{thread_id}/runs/{run_id}")
        # Parse message if present
        if "message" in resp and resp["message"]:
            msg_data = resp["message"]
            # Parse content blocks
            if "content" in msg_data:
                msg_data["content"] = [MessageContent(**c) for c in msg_data["content"]]
            # Parse attachments (Pixi tools only)
            if "sources" in msg_data and msg_data["sources"]:
                msg_data["sources"] = [MessageSource(**s) for s in msg_data["sources"]]
            if "media" in msg_data and msg_data["media"]:
                msg_data["media"] = [MessageMedia(**m) for m in msg_data["media"]]
            if "code" in msg_data and msg_data["code"]:
                msg_data["code"] = [MessageCode(**c) for c in msg_data["code"]]
            resp["message"] = ThreadMessage(**msg_data)
        return Run(**resp)

    def wait_for_run(
        self, thread_id: str, run_id: str, poll_interval: float = 0.5
    ) -> Run:
        """
        Poll until run completes.

        Args:
            thread_id: Thread ID
            run_id: Run ID
            poll_interval: Polling interval in seconds (default: 0.5)

        Returns:
            Completed run

        Raises:
            RuntimeError: If run fails or is cancelled
        """
        while True:
            run = self.get_run(thread_id, run_id)

            if run.status == "completed":
                return run
            elif run.status == "failed":
                raise RuntimeError("Run failed")
            elif run.status == "cancelled":
                raise RuntimeError("Run cancelled")

            time.sleep(poll_interval)

    def list_assistants(self) -> List[Assistant]:
        """List all assistants."""
        resp = self._request("GET", "/assistants")
        return [Assistant(**a) for a in resp["data"]]

    def get_assistant(self, assistant_id: str) -> Assistant:
        """Get assistant by ID."""
        resp = self._request("GET", f"/assistants/{assistant_id}")
        return Assistant(**resp)

    def create_assistant(
        self, name: str, instructions: str, tools_config: Optional[str] = None
    ) -> Assistant:
        """Create a new assistant."""
        data = {"name": name, "instructions": instructions}
        if tools_config:
            data["tools_config"] = tools_config

        resp = self._request("POST", "/assistants", json=data)
        return Assistant(**resp)

    def update_assistant(
        self,
        assistant_id: str,
        name: str,
        instructions: str,
        tools_config: Optional[str] = None,
    ) -> Assistant:
        """Update an assistant."""
        data = {"name": name, "instructions": instructions}
        if tools_config:
            data["tools_config"] = tools_config

        resp = self._request("PUT", f"/assistants/{assistant_id}", json=data)
        return Assistant(**resp)

    def delete_assistant(self, assistant_id: str) -> None:
        """Delete an assistant."""
        self._request("DELETE", f"/assistants/{assistant_id}")

    def list_assistant_threads(
        self, assistant_id: str, limit: int = 20
    ) -> List[Thread]:
        """
        List all threads used by an assistant.

        Args:
            assistant_id: Assistant ID
            limit: Maximum threads to return (default: 20)

        Returns:
            List of threads that have runs for this assistant
        """
        resp = self._request("GET", f"/assistants/{assistant_id}/threads?limit={limit}")
        return [Thread(**t) for t in resp["data"]]

    def analyze_image(self, request: VisionAnalyzeRequest) -> VisionAnalyzeResponse:
        """
        Analyze an image and return a detailed description.

        The server downloads and preprocesses the image (resize, convert to JPEG).
        For soulkyn.com URLs, Cloudflare bypass is automatically applied.

        Example:
            >>> response = client.analyze_image(
            ...     VisionAnalyzeRequest(
            ...         image_url="https://example.com/image.jpg",
            ...         user_prompt="Describe this in detail.",
            ...     )
            ... )
            >>> print(response.result)
        """
        data = {"image_url": request.image_url}
        if request.user_prompt:
            data["user_prompt"] = request.user_prompt

        resp = self._request("POST", "/vision/analyze", json=data)
        return VisionAnalyzeResponse(
            result=resp["result"],
            usage=VisionUsage(**resp["usage"]),
        )

    def analyze_image_for_tags(self, request: VisionTagsRequest) -> VisionTagsResponse:
        """
        Generate comma-separated tags for an image.

        Returns short tags suitable for categorization and search.

        Example:
            >>> response = client.analyze_image_for_tags(
            ...     VisionTagsRequest(image_url="https://example.com/image.jpg")
            ... )
            >>> print(response.result)
        """
        resp = self._request("POST", "/vision/tags", json={"image_url": request.image_url})
        return VisionTagsResponse(
            result=resp["result"],
            usage=VisionUsage(**resp["usage"]),
        )

    def extract_text(self, request: VisionOCRRequest) -> VisionOCRResponse:
        """
        Perform OCR on an image and return extracted text.

        Preserves structure (tables, lists, hierarchy) and uses high detail mode.

        Example:
            >>> response = client.extract_text(
            ...     VisionOCRRequest(image_url="https://example.com/document.jpg")
            ... )
            >>> print(response.result)
        """
        resp = self._request("POST", "/vision/ocr", json={"image_url": request.image_url})
        return VisionOCRResponse(
            result=resp["result"],
            usage=VisionUsage(**resp["usage"]),
        )

    def analyze_video(self, request: VisionVideoRequest) -> VisionVideoResponse:
        """
        Analyze a video and return a description of the content.

        Videos must be under 10MB. The server performs size check via HEAD request.
        For soulkyn.com URLs, Cloudflare bypass is automatically applied.

        Example:
            >>> response = client.analyze_video(
            ...     VisionVideoRequest(
            ...         video_url="https://example.com/video.mp4",
            ...         user_prompt="Describe what happens.",
            ...     )
            ... )
            >>> print(response.result)
        """
        data = {"video_url": request.video_url}
        if request.user_prompt:
            data["user_prompt"] = request.user_prompt

        resp = self._request("POST", "/vision/video", json=data)
        return VisionVideoResponse(
            result=resp["result"],
            usage=VisionUsage(**resp["usage"]),
        )

    def moderate_text(self, request: ModerationTextRequest) -> ModerationResponse:
        """
        Classify text content into 11 categories with confidence scores.

        Categories: UNDERAGE_SEXUAL (priority), JAILBREAK, SUICIDE_SELF_HARM, PII,
        COPYRIGHT_VIOLATION, VIOLENT, ILLEGAL_ACTS, UNETHICAL, HATE_SPEECH,
        SEXUAL_ADULT, SAFE.

        Score ranges: 1.00 = perfect match, 0.90-0.99 = very strong, 0.70-0.89 = strong,
        0.50-0.69 = moderate, 0.00-0.49 = weak.

        Example:
            >>> response = client.moderate_text(
            ...     ModerationTextRequest(prompt="text to moderate")
            ... )
            >>> print(f"{response.category} (score: {response.score})")
        """
        resp = self._request("POST", "/moderations", json={"prompt": request.prompt})
        return ModerationResponse(
            category=resp["category"],
            score=resp["score"],
            usage=VisionUsage(**resp["usage"]),
        )

    def moderate_media(self, request: ModerationMediaRequest) -> ModerationResponse:
        """
        Classify image or video content into 11 categories with confidence scores.

        Same categories as moderate_text but with visual assessment.
        SEXUAL_ADULT = visible genitals OR active sex acts only.
        SAFE = cleavage, lingerie, bikinis, clothed, suggestive.

        Example:
            >>> response = client.moderate_media(
            ...     ModerationMediaRequest(
            ...         media_url="https://example.com/image.jpg",
            ...         is_video=False,
            ...     )
            ... )
            >>> print(f"{response.category} (score: {response.score})")
        """
        data = {"media_url": request.media_url, "is_video": request.is_video}
        resp = self._request("POST", "/moderations/media", json=data)
        return ModerationResponse(
            category=resp["category"],
            score=resp["score"],
            usage=VisionUsage(**resp["usage"]),
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.session.close()
