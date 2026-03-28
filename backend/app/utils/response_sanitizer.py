"""Helpers for removing model reasoning traces from responses."""

from __future__ import annotations

import re

THINK_BLOCK_PATTERN = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)
THINK_OPEN_TAG = "<think>"
THINK_CLOSE_TAG = "</think>"
FALLBACK_RESPONSE = "I had a little thought bubble there. Ask again and I'll keep it clean and punchy. 😄"


def strip_reasoning_blocks(text: str) -> str:
    """Remove any `<think>...</think>` blocks from a response."""

    return THINK_BLOCK_PATTERN.sub("", text)


def sanitize_response_text(text: str, fallback_message: str = FALLBACK_RESPONSE) -> str:
    """Strip reasoning blocks, trim the result, and provide a friendly fallback if needed."""

    sanitized = strip_reasoning_blocks(text).strip()
    return sanitized or fallback_message


class StreamingResponseSanitizer:
    """Stateful sanitizer for filtering reasoning tags from streamed model output."""

    def __init__(self, fallback_message: str = FALLBACK_RESPONSE) -> None:
        self.fallback_message = fallback_message
        self._inside_think_block = False
        self._pending = ""
        self._visible_parts: list[str] = []
        self._started_visible_output = False

    def push(self, chunk: str) -> str:
        """Consume a raw streamed chunk and return the visible safe portion."""

        return self._consume(chunk, final=False)

    def finalize(self) -> tuple[str, str]:
        """Flush any remaining visible content and return the final sanitized reply."""

        trailing_chunk = self._consume("", final=True)
        final_reply = "".join(self._visible_parts).strip()
        if not final_reply:
            final_reply = self.fallback_message
        return trailing_chunk, final_reply

    def _consume(self, chunk: str, *, final: bool) -> str:
        self._pending += chunk
        visible_output: list[str] = []

        while self._pending:
            pending_lower = self._pending.lower()

            if self._inside_think_block:
                end_index = pending_lower.find(THINK_CLOSE_TAG)
                if end_index == -1:
                    if final:
                        self._pending = ""
                    else:
                        self._pending = self._pending[-(len(THINK_CLOSE_TAG) - 1) :]
                    break

                self._pending = self._pending[end_index + len(THINK_CLOSE_TAG) :]
                self._inside_think_block = False
                continue

            start_index = pending_lower.find(THINK_OPEN_TAG)
            if start_index != -1:
                visible_output.append(self._pending[:start_index])
                self._pending = self._pending[start_index + len(THINK_OPEN_TAG) :]
                self._inside_think_block = True
                continue

            if final:
                visible_output.append(self._pending)
                self._pending = ""
                break

            keep_length = min(len(THINK_OPEN_TAG) - 1, len(self._pending))
            if len(self._pending) > keep_length:
                visible_output.append(self._pending[:-keep_length])
            self._pending = self._pending[-keep_length:] if keep_length else ""
            break

        visible_text = "".join(visible_output)
        if not self._started_visible_output:
            visible_text = visible_text.lstrip()

        if visible_text:
            self._started_visible_output = True
            self._visible_parts.append(visible_text)

        return visible_text

