import httpx
import orjson
from typing import AsyncIterator, List, Optional, Dict, Any
from .models import (
    ChatCompletionRequest,
    ChatCompletionChunk,
    ChatCompletionResponse,
    Message,
    JarvisOptions,
)


class JarvisClient:
    def __init__(
        self,
        base_url: str,
        user_id: str,
        jarvis_options: Optional[JarvisOptions] = None,
        timeout: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.jarvis_options = jarvis_options or JarvisOptions()
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        # Close the HTTP client
        await self.client.aclose()

    async def chat_completion(
        self,
        messages: List[Message],
        conversation_id: Optional[str] = None,
        stream: bool = True,
    ) -> ChatCompletionResponse:
        # Send non-streaming chat completion request
        if stream:
            raise ValueError("Use chat_completion_stream() for streaming requests")

        # Update conversation_id in jarvis_options if provided
        jarvis_options = self.jarvis_options.model_copy()
        if conversation_id:
            jarvis_options.conversation_id = conversation_id

        request = ChatCompletionRequest(
            model="jarvis-chat",
            messages=messages,
            stream=False,
            user=self.user_id,
            jarvis_options=jarvis_options,
        )

        url = f"{self.base_url}/chat/completions"

        try:
            response = await self.client.post(
                url,
                json=request.model_dump(),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            return ChatCompletionResponse(**data)
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to send chat completion: {e}")

    async def chat_completion_stream(
        self,
        messages: List[Message],
        conversation_id: Optional[str] = None,
    ) -> AsyncIterator[ChatCompletionChunk]:
        # Send streaming chat completion request and yield chunks
        # Update conversation_id in jarvis_options if provided
        jarvis_options = self.jarvis_options.model_copy()
        if conversation_id:
            jarvis_options.conversation_id = conversation_id

        request = ChatCompletionRequest(
            model="jarvis-chat",
            messages=messages,
            stream=True,
            user=self.user_id,
            jarvis_options=jarvis_options,
        )

        url = f"{self.base_url}/chat/completions"

        try:
            async with self.client.stream(
                "POST",
                url,
                json=request.model_dump(),
                headers={"Content-Type": "application/json"},
            ) as response:
                response.raise_for_status()

                # Parse SSE stream
                async for chunk in self._parse_sse_stream(response):
                    yield chunk

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to stream chat completion: {e}")

    async def _parse_sse_stream(
        self, response: httpx.Response
    ) -> AsyncIterator[ChatCompletionChunk]:
        # Parse Server-Sent Events (SSE) stream
        buffer = ""

        async for line_bytes in response.aiter_lines():
            line = line_bytes.strip()

            # Skip empty lines
            if not line:
                continue

            # Check for [DONE] marker
            if line == "data: [DONE]":
                break

            # Parse data: prefix
            if line.startswith("data: "):
                data_str = line[6:]  # Remove "data: " prefix

                try:
                    # Parse JSON
                    data = orjson.loads(data_str)

                    # Validate and yield chunk
                    chunk = ChatCompletionChunk(**data)
                    yield chunk

                except orjson.JSONDecodeError:
                    # Skip invalid JSON
                    continue
                except Exception:
                    # Skip invalid chunks
                    continue

    async def get_conversation_history(
        self, conversation_id: str
    ) -> Dict[str, Any]:
        # Get conversation history
        url = f"{self.base_url}/conversations/{conversation_id}"
        params = {"user_id": self.user_id}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to get conversation history: {e}")

    async def list_user_conversations(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Dict[str, Any]:
        # List user's conversations
        url = f"{self.base_url}/users/{self.user_id}/conversations"
        params = {}

        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        try:
            response = await self.client.get(url, params=params if params else None)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to list conversations: {e}")

    async def delete_conversation(self, conversation_id: str) -> Dict[str, Any]:
        # Delete a conversation
        url = f"{self.base_url}/conversations/{conversation_id}"
        params = {"user_id": self.user_id}

        try:
            response = await self.client.delete(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete conversation: {e}")

    async def submit_feedback(
        self, session_id: str, feedback: str
    ) -> Dict[str, Any]:
        # Submit feedback (positive/negative)
        url = f"{self.base_url}/feedback"
        data = {
            "user_id": self.user_id,
            "session_id": session_id,
            "feedback": feedback,
        }

        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to submit feedback: {e}")
