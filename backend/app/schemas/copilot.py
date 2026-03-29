"""Pydantic schemas per il Copilot."""
from pydantic import BaseModel, Field


class CopilotMessage(BaseModel):
    """Singolo messaggio nella conversazione."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class CopilotChatRequest(BaseModel):
    """Request body per /copilot/chat."""
    messages: list[CopilotMessage] = Field(..., min_length=1)
    context: dict | None = Field(None, description="Contesto corrente: pagina, dati selezionati")
