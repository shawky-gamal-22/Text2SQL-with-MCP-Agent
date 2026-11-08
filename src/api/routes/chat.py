from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None


@router.post("")
async def chat(body: ChatRequest, request: Request) -> StreamingResponse:
    service: ChatService | None = getattr(request.app.state, "chat_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Chat service is not available.")

    events: AsyncIterator[str] = service.stream_response(
        message=body.message,
        conversation_id=body.conversation_id,
    )
    return StreamingResponse(
        events,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )