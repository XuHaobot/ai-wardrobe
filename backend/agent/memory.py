"""
对话记忆系统 - 多轮对话管理
"""
import uuid
import time
from dataclasses import dataclass, field


@dataclass
class ConversationTurn:
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    timestamp: float = field(default_factory=time.time)
    tool_call_id: str = ""


@dataclass
class ConversationSession:
    session_id: str
    user_id: int
    turns: list[ConversationTurn] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def add_message(self, role: str, content: str, tool_call_id: str = ""):
        self.turns.append(ConversationTurn(
            role=role,
            content=content,
            tool_call_id=tool_call_id,
        ))

    def get_context_window(self, max_turns: int = 20) -> list[dict]:
        """获取最近N轮对话作为上下文窗口"""
        recent = self.turns[-max_turns:]
        result = []
        for t in recent:
            msg = {"role": t.role, "content": t.content}
            if t.tool_call_id:
                msg["tool_call_id"] = t.tool_call_id
            result.append(msg)
        return result


class MemoryManager:
    """记忆管理器 - 管理所有活跃会话"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions = {}
        return cls._instance

    def create_session(self, user_id: int) -> str:
        """创建新会话"""
        session_id = f"session-{uuid.uuid4().hex[:12]}"
        session = ConversationSession(session_id=session_id, user_id=user_id)
        # 注入系统提示
        session.add_message("system", self._get_system_prompt())
        self._sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> ConversationSession:
        return self._sessions.get(session_id)

    def has_session(self, session_id: str) -> bool:
        return session_id in self._sessions

    def _get_system_prompt(self) -> str:
        return """你是AI智能衣橱助手，一个专业的穿搭顾问。你可以帮助用户：
1. 搜索衣橱中的衣物（支持自然语言描述，如"找一条蓝色牛仔裤"）
2. 根据天气和场合推荐穿搭方案
3. 查询实时天气信息
4. 分析衣物搭配建议
5. 提供穿搭风格和配色建议

请始终基于用户衣橱中的实际衣物给出建议，不要编造不存在的衣物。
回答要专业、友好、有实用性。"""
