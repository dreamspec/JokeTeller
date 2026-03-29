"""LM Studio integration service using the OpenAI-compatible local API."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import (
    EmptyModelResponseError,
    InvalidModelError,
    LMStudioTimeoutError,
    LMStudioUnavailableError,
    UpstreamProtocolError,
)
from app.models.chat import ChatRequest, ChatResponse
from app.models.status import LMStudioStatus
from app.services.prompt_builder import build_messages
from app.utils.response_sanitizer import StreamingResponseSanitizer, sanitize_response_text
from app.utils.sse import format_sse


class LMStudioService:
    """Encapsulates all communication with LM Studio."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.lm_studio_timeout_seconds, connect=5.0)
        )

    async def aclose(self) -> None:
        """Close the shared async client."""

        await self._client.aclose()

    async def probe(self) -> LMStudioStatus:
        """Return a status payload without raising user-facing exceptions."""

        try:
            models = await self.list_models()
            return LMStudioStatus(
                reachable=True,
                base_url=self.settings.normalized_lm_studio_base_url,
                default_model=self.settings.lm_studio_default_model or None,
                available_models=models,
                error=None,
            )
        except (LMStudioUnavailableError, LMStudioTimeoutError, UpstreamProtocolError) as exc:
            return LMStudioStatus(
                reachable=False,
                base_url=self.settings.normalized_lm_studio_base_url,
                default_model=self.settings.lm_studio_default_model or None,
                available_models=[],
                error=exc.message,
            )

    async def list_models(self) -> list[str]:
        """Fetch the list of models exposed by LM Studio."""

        response = await self._request("GET", "/models")
        data = self._parse_json_response(response)
        items = data.get("data")
        if not isinstance(items, list):
            raise UpstreamProtocolError("LM Studio returned an unexpected models payload.")

        model_ids = [item.get("id") for item in items if isinstance(item, dict) and item.get("id")]
        return [model_id for model_id in model_ids if isinstance(model_id, str)]

    async def resolve_model(self, requested_model: str | None) -> str:
        """Choose the requested model or a safe fallback from LM Studio."""

        available_models = await self.list_models()
        candidate = requested_model or self.settings.lm_studio_default_model or None

        if not candidate and available_models:
            candidate = available_models[0]

        if not candidate:
            raise InvalidModelError(
                "No model is currently loaded in LM Studio.",
                suggestion="Load a model in LM Studio, or set LM_STUDIO_DEFAULT_MODEL in your .env file.",
            )

        if available_models and candidate not in available_models:
            suggestion = f"Available models: {', '.join(available_models[:5])}"
            raise InvalidModelError(
                f"Model `{candidate}` is not available in LM Studio.",
                suggestion=suggestion,
            )

        return candidate

    async def chat(self, chat_request: ChatRequest) -> ChatResponse:
        """Run a non-streaming chat completion."""

        model_name = await self.resolve_model(chat_request.model)
        payload = self._build_payload(chat_request=chat_request, model_name=model_name, stream=False)
        response = await self._request("POST", "/chat/completions", json=payload)
        data = self._parse_json_response(response)
        reply = self._extract_reply_text(data)
        finish_reason = self._extract_finish_reason(data)
        return ChatResponse(reply=reply, model=model_name, finish_reason=finish_reason)

    async def stream_chat(self, chat_request: ChatRequest) -> AsyncIterator[str]:
        """Run a streaming chat completion and yield SSE-formatted events."""

        try:
            model_name = await self.resolve_model(chat_request.model)
            payload = self._build_payload(chat_request=chat_request, model_name=model_name, stream=True)
            sanitizer = StreamingResponseSanitizer()
            yielded_visible_text = False
            received_model_text = False

            async with self._client.stream(
                "POST",
                self._url("/chat/completions"),
                json=payload,
            ) as response:
                await self._ensure_success(response)

                async for raw_line in response.aiter_lines():
                    if not raw_line:
                        continue

                    line = raw_line.strip()
                    if not line.startswith("data:"):
                        continue

                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break

                    chunk = self._parse_stream_chunk(data_str)
                    if chunk is None:
                        continue

                    received_model_text = True
                    visible_chunk = sanitizer.push(chunk)
                    if visible_chunk:
                        yielded_visible_text = True
                        yield format_sse("chunk", {"content": visible_chunk, "model": model_name})

                if not received_model_text:
                    raise EmptyModelResponseError()

                trailing_chunk, final_reply = sanitizer.finalize()
                if trailing_chunk:
                    yielded_visible_text = True
                    yield format_sse("chunk", {"content": trailing_chunk, "model": model_name})
                elif not yielded_visible_text and final_reply:
                    yield format_sse("chunk", {"content": final_reply, "model": model_name})

                yield format_sse("done", {"model": model_name, "reply": final_reply})
        except (
            LMStudioUnavailableError,
            LMStudioTimeoutError,
            InvalidModelError,
            EmptyModelResponseError,
            UpstreamProtocolError,
        ) as exc:
            yield format_sse("error", exc.to_payload())

    def _build_payload(self, *, chat_request: ChatRequest, model_name: str, stream: bool) -> dict[str, Any]:
        """Create the payload expected by LM Studio's OpenAI-compatible API."""

        return {
            "model": model_name,
            "messages": build_messages(
                chat_request=chat_request,
                max_history_messages=self.settings.max_history_messages,
                model_name=model_name,
            ),
            "temperature": chat_request.temperature,
            "max_tokens": chat_request.max_tokens,
            "top_p": chat_request.top_p,
            "stream": stream,
        }

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Send a request to LM Studio and translate transport failures."""

        try:
            response = await self._client.request(method, self._url(path), **kwargs)
        except httpx.TimeoutException as exc:
            raise LMStudioTimeoutError() from exc
        except httpx.HTTPError as exc:
            raise LMStudioUnavailableError(
                "LM Studio is not reachable from the backend.",
                suggestion="Check that LM Studio is open and its local server is enabled.",
            ) from exc

        await self._ensure_success(response)
        return response

    async def _ensure_success(self, response: httpx.Response) -> None:
        """Raise a friendly exception when LM Studio responds with an error."""

        if response.is_success:
            return

        response_text = await response.aread()
        message = self._extract_error_message(response_text)

        if response.status_code in {400, 404} and "model" in message.lower():
            raise InvalidModelError(message)

        raise LMStudioUnavailableError(
            message or "LM Studio returned an unexpected error.",
            suggestion="Confirm the local server is enabled and the configured base URL is correct.",
        )

    @staticmethod
    def _parse_json_response(response: httpx.Response) -> dict[str, Any]:
        """Parse a JSON response into a dictionary."""

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise UpstreamProtocolError("LM Studio returned a non-JSON response.") from exc

        if not isinstance(data, dict):
            raise UpstreamProtocolError("LM Studio returned an unexpected JSON payload.")
        return data

    @staticmethod
    def _extract_reply_text(data: dict[str, Any]) -> str:
        """Extract the final assistant message from a chat completion response."""

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise UpstreamProtocolError("LM Studio returned no completion choices.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise UpstreamProtocolError("LM Studio returned an invalid completion choice.")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise UpstreamProtocolError("LM Studio returned an invalid completion message.")

        content = message.get("content")
        extracted_text = LMStudioService._coerce_content_to_text(content, strip_text=False)
        if extracted_text == "":
            raise EmptyModelResponseError()
        return sanitize_response_text(extracted_text)

    @staticmethod
    def _extract_finish_reason(data: dict[str, Any]) -> str | None:
        """Extract the finish reason from a completion response."""

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            return None
        finish_reason = choices[0].get("finish_reason")
        return finish_reason if isinstance(finish_reason, str) else None

    @staticmethod
    def _parse_stream_chunk(data_str: str) -> str | None:
        """Parse a single streaming chunk into plain text."""

        try:
            payload = json.loads(data_str)
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, dict):
            return None

        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            return None

        delta = choices[0].get("delta")
        if not isinstance(delta, dict):
            return None

        if "content" not in delta:
            return None
        return LMStudioService._coerce_content_to_text(delta.get("content"), strip_text=False)

    @staticmethod
    def _coerce_content_to_text(content: Any, *, strip_text: bool = True) -> str:
        """Convert OpenAI-style string or list content payloads into plain text."""

        if isinstance(content, str):
            return content.strip() if strip_text else content

        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    text_parts.append(item["text"])
            joined_text = "".join(text_parts)
            return joined_text.strip() if strip_text else joined_text

        return ""

    @staticmethod
    def _extract_error_message(raw_body: bytes) -> str:
        """Extract a friendly error message from an error response body."""

        if not raw_body:
            return ""

        try:
            parsed = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return raw_body.decode("utf-8", errors="ignore").strip()

        if isinstance(parsed, dict):
            if isinstance(parsed.get("error"), dict):
                error_message = parsed["error"].get("message")
                if isinstance(error_message, str):
                    return error_message
            if isinstance(parsed.get("message"), str):
                return parsed["message"]

        return str(parsed)

    def _url(self, path: str) -> str:
        """Build a full LM Studio URL from a relative API path."""

        return f"{self.settings.normalized_lm_studio_base_url}{path}"
