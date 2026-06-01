from pydantic import BaseModel
from typing import Any


class UnifiedMessage(BaseModel):
    role: str
    content: str


class UnifiedRequest(BaseModel):
    model: str
    messages: list[UnifiedMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    top_p: float | None = None


class UnifiedChoice(BaseModel):
    index: int
    message: UnifiedMessage | None = None
    delta: dict | None = None
    finish_reason: str | None = None


class UnifiedUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class UnifiedResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    model: str
    choices: list[UnifiedChoice]
    usage: UnifiedUsage | None = None
    provider: str = ""
