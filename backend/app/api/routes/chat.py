"""Chat endpoints."""

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.models.chat import ChatRequest, ChatResponse
from app.services.lm_studio import LMStudioService

router = APIRouter(tags=["chat"])


def get_lm_studio_service(request: Request) -> LMStudioService:
    """Fetch the shared LM Studio service instance."""

    return request.app.state.lm_studio_service


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    lm_studio_service: LMStudioService = Depends(get_lm_studio_service),
) -> ChatResponse:
    """Return a complete non-streaming chat response."""

    return await lm_studio_service.chat(chat_request)


@router.post("/chat/stream")
async def stream_chat(
    chat_request: ChatRequest,
    lm_studio_service: LMStudioService = Depends(get_lm_studio_service),
) -> StreamingResponse:
    """Stream chat chunks to the frontend as SSE."""

    async def event_stream() -> AsyncIterator[str]:
        async for event in lm_studio_service.stream_chat(chat_request):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

