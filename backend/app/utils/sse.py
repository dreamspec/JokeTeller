"""Helpers for formatting SSE messages."""

from __future__ import annotations

import json
from typing import Any


def format_sse(event: str, data: dict[str, Any]) -> str:
    """Format an event and payload as a Server-Sent Event string."""

    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

