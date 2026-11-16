import json
import uuid
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import get_settings
from .faq import SYSTEM_PROMPT, should_escalate
from .llm import LLMError, chat_completion

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation store (sufficient for local single-user demos)
SESSIONS: dict[str, list[dict[str, str]]] = {}

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=64)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    escalate: bool
    category: str
    confidence: float
    history: list[dict[str, str]]


class SessionCreateResponse(BaseModel):
    session_id: str


def _parse_llm_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "reply": raw.strip(),
            "escalate": False,
            "category": "other",
            "confidence": 0.5,
        }


@app.get("/api/health")
async def health() -> dict:
    configured = bool(settings.openrouter_api_key) and not settings.openrouter_api_key.startswith(
        "your_"
    )
    return {
        "status": "ok",
        "app": settings.app_name,
        "llm_configured": configured,
        "model": settings.openrouter_model,
    }


@app.post("/api/session", response_model=SessionCreateResponse)
async def create_session() -> SessionCreateResponse:
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = []
    return SessionCreateResponse(session_id=session_id)


@app.get("/api/history/{session_id}")
async def get_history(session_id: str) -> dict:
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"session_id": session_id, "history": SESSIONS[session_id]}


@app.delete("/api/history/{session_id}")
async def clear_history(session_id: str) -> dict:
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    SESSIONS[session_id] = []
    return {"session_id": session_id, "cleared": True}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    session_id = payload.session_id or str(uuid.uuid4())
    history = SESSIONS.setdefault(session_id, [])

    user_message = payload.message.strip()
    if not user_message:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history[-12:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        raw = await chat_completion(messages, temperature=0.3)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    parsed = _parse_llm_json(raw)
    reply = str(parsed.get("reply") or "I'm sorry — I could not generate a response.")
    llm_escalate = bool(parsed.get("escalate", False))
    escalate = should_escalate(user_message, llm_escalate)
    category = str(parsed.get("category") or "other")
    try:
        confidence = float(parsed.get("confidence", 0.7))
    except (TypeError, ValueError):
        confidence = 0.7

    if escalate:
        reply += (
            "\n\nI've flagged this for a human support agent. "
            "A specialist will follow up during business hours (Mon–Fri 9:00–18:00 UTC)."
        )

    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    SESSIONS[session_id] = history

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        escalate=escalate,
        category=category,
        confidence=confidence,
        history=history,
    )


@app.get("/")
async def serve_index() -> FileResponse:
    index = FRONTEND_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return FileResponse(index)


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def run() -> None:
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
