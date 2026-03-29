"""Copilot API — streaming chat endpoint con orchestrazione agenti."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import DbSession
from app.schemas.copilot import CopilotChatRequest
from app.services.copilot_service import stream_chat

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/chat")
async def chat(body: CopilotChatRequest, session: DbSession):
    """Streaming chat con il Copilot AI.

    Restituisce Server-Sent Events (SSE) con i seguenti tipi:
    - text: chunk di testo della risposta
    - tool_use: il copilot sta usando un tool
    - tool_result: risultato del tool
    - done: risposta completata
    - error: errore
    """
    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    return StreamingResponse(
        stream_chat(messages, session, body.context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
