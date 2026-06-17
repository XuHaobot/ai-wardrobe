"""
AI 对话路由 - 流式Chat + Agent
"""
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from main_deps import get_current_user_id

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


@router.post("/api/chat/stream")
async def chat_stream(
    body: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """流式AI对话接口（SSE）"""
    from agent.core import AgentCore
    from agent.memory import MemoryManager

    memory = MemoryManager()
    session_id = body.session_id
    if not session_id or not memory.has_session(session_id):
        session_id = memory.create_session(user_id)

    agent = AgentCore(user_id=user_id, db=db)

    async def generate():
        # 先发送session_id
        yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id}, ensure_ascii=False)}\n\n"

        # Agent处理
        session = memory.get_session(session_id)
        history = session.get_context_window()

        async for event in agent.chat_stream(body.question, history):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/api/chat")
async def chat(
    body: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """非流式AI对话接口"""
    from agent.core import AgentCore
    from agent.memory import MemoryManager

    memory = MemoryManager()
    session_id = body.session_id
    if not session_id or not memory.has_session(session_id):
        session_id = memory.create_session(user_id)

    agent = AgentCore(user_id=user_id, db=db)
    session = memory.get_session(session_id)
    history = session.get_context_window()

    result = await agent.chat(body.question, history)
    session.add_message("user", body.question)
    session.add_message("assistant", result["answer"])

    return {
        "code": 1,
        "data": {
            "answer": result["answer"],
            "agent_trace": result.get("agent_trace", []),
            "session_id": session_id,
        },
    }
