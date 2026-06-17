"""
Agent Core - 基于 Function Calling 的智能体
"""
import json
from typing import AsyncGenerator

import httpx
from sqlalchemy.orm import Session

from config import get_settings
from agent.tools import AGENT_TOOLS
from agent.tool_executor import ToolExecutor


class AgentCore:
    """基于 OpenAI Function Calling 协议的 Agent"""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db
        self.settings = get_settings()
        self.max_iterations = 5
        self.tool_executor = ToolExecutor(user_id, db)

    async def chat(self, user_message: str, history: list[dict] = None) -> dict:
        """非流式对话"""
        messages = list(history or [])
        messages.append({"role": "user", "content": user_message})

        trace = []

        for iteration in range(self.max_iterations):
            response = await self._call_llm(messages)

            tool_calls = response.get("tool_calls")
            if not tool_calls:
                # LLM 直接回复
                return {
                    "answer": response.get("content", "抱歉，我无法回答这个问题。"),
                    "agent_trace": trace,
                    "total_iterations": iteration + 1,
                }

            # 添加assistant消息
            messages.append(response)

            # 执行工具调用
            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                try:
                    func_args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    func_args = {}

                result = await self.tool_executor.execute(func_name, func_args)

                trace.append({
                    "iteration": iteration + 1,
                    "tool": func_name,
                    "args": func_args,
                    "result_preview": result[:200],
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result,
                })

        # 超过最大迭代次数
        return {
            "answer": "抱歉，处理你的请求时遇到了问题，请尝试简化问题后重试。",
            "agent_trace": trace,
            "total_iterations": self.max_iterations,
        }

    async def chat_stream(
        self, user_message: str, history: list[dict] = None
    ) -> AsyncGenerator[dict, None]:
        """流式对话（SSE）"""
        messages = list(history or [])
        messages.append({"role": "user", "content": user_message})

        trace = []

        for iteration in range(self.max_iterations):
            yield {"type": "thinking", "message": f"Agent 正在思考... (第{iteration + 1}轮)"}

            response = await self._call_llm(messages)

            tool_calls = response.get("tool_calls")
            if not tool_calls:
                # 最终回答
                yield {
                    "type": "answer",
                    "answer": response.get("content", ""),
                    "agent_trace": trace,
                }
                return

            # 添加工具调用信息
            messages.append(response)

            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                try:
                    func_args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    func_args = {}

                yield {
                    "type": "tool_call",
                    "tool": func_name,
                    "args": func_args,
                }

                result = await self.tool_executor.execute(func_name, func_args)

                trace.append({
                    "iteration": iteration + 1,
                    "tool": func_name,
                    "args": func_args,
                    "result_preview": result[:200],
                })

                yield {
                    "type": "tool_result",
                    "tool": func_name,
                    "result_preview": result[:300],
                }

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result,
                })

        yield {
            "type": "answer",
            "answer": "抱歉，处理你的请求时遇到了问题，请尝试简化问题后重试。",
            "agent_trace": trace,
        }

    async def _call_llm(self, messages: list[dict]) -> dict:
        """调用通义千问 API（兼容 OpenAI Function Calling 格式）"""
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.dashscope_api_key}",
            "Content-Type": "application/json",
        }

        # 清理消息中的tool_calls字段格式
        cleaned_messages = []
        for msg in messages:
            m = {"role": msg["role"], "content": msg.get("content", "")}
            if "tool_calls" in msg:
                m["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg:
                m["tool_call_id"] = msg["tool_call_id"]
            cleaned_messages.append(m)

        payload = {
            "model": self.settings.qwen_text_model,
            "messages": cleaned_messages,
            "tools": AGENT_TOOLS,
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json=payload)

        data = resp.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        return message
