"""Pydantic models for chat requests and responses."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class JokeStyle(str, Enum):
    """Available joke flavors for the assistant."""

    RANDOM = "random"
    DAD = "dad"
    PUN = "pun"
    SARCASTIC = "sarcastic"
    DARK_SAFE = "dark_safe"
    GEEK = "geek"
    WHOLESOME = "wholesome"


class AnswerStyle(str, Enum):
    """Supported response verbosity modes."""

    SHORT = "short"
    NORMAL = "normal"


class ChatMessage(BaseModel):
    """A single user or assistant message."""

    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4_000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message content cannot be empty.")
        return stripped


class ChatRequest(BaseModel):
    """Payload used for both streaming and non-streaming chat endpoints."""

    message: str = Field(..., min_length=1, max_length=4_000)
    history: list[ChatMessage] = Field(default_factory=list)
    system_prompt: str | None = Field(default=None, max_length=4_000)
    joke_style: JokeStyle = JokeStyle.RANDOM
    answer_style: AnswerStyle = AnswerStyle.NORMAL
    model: str | None = Field(default=None, max_length=200)
    temperature: float = Field(default=0.8, ge=0.0, le=2.0)
    max_tokens: int = Field(default=220, ge=32, le=1_024)
    top_p: float = Field(default=0.95, gt=0.0, le=1.0)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message cannot be empty.")
        return stripped

    @field_validator("system_prompt")
    @classmethod
    def normalize_system_prompt(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("model")
    @classmethod
    def normalize_model(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ChatResponse(BaseModel):
    """Backend response returned from the non-streaming chat endpoint."""

    reply: str
    model: str
    finish_reason: str | None = None

