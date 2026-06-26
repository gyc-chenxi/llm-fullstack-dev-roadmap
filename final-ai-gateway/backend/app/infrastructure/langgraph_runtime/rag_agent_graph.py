"""
LangGraph Agent Graph — RAG agent with state machine:
classify → retrieve → plan → execute → verify → answer
"""

from __future__ import annotations

import logging
import time
from typing import Any, AsyncIterator, Literal, TypedDict

from app.domain.entities.fault_event import FaultType
from app.domain.services.agent_loop_guard import AgentLoopGuard
from app.infrastructure.langgraph_runtime.redis_checkpointer import RedisCheckpointer
from app.infrastructure.langgraph_runtime.tool_registry import ToolRegistry
from app.infrastructure.llm_clients.gateway_chat_model import GatewayChatModel
from app.infrastructure.retrieval.hybrid_retriever import HybridRetriever
from app.infrastructure.retrieval.reranker import Reranker

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    run_id: str
    goal: str
    task_type: str | None
    messages: list[dict]
    retrieved_docs: list[dict]
    planned_tools: list[str]
    tool_results: list[dict]
    draft_answer: str | None
    final_answer: str | None
    step: int
    errors: list[dict]
    node_name: str
    event_id: int


class RagAgentGraph:
    def __init__(
        self,
        gateway_model: GatewayChatModel,
        retriever: HybridRetriever,
        reranker: Reranker,
        tool_registry: ToolRegistry,
        checkpointer: RedisCheckpointer,
        loop_guard: AgentLoopGuard,
    ):
        self.gateway_model = gateway_model
        self.retriever = retriever
        self.reranker = reranker
        self.tool_registry = tool_registry
        self.checkpointer = checkpointer
        self.loop_guard = loop_guard
        self._event_id = 0

    async def run(self, run_id: str, goal: str, agent_type: str = "rag_agent",
                   max_steps: int = 20) -> AsyncIterator[dict]:
        state: AgentState = {
            "run_id": run_id,
            "goal": goal,
            "task_type": None,
            "messages": [],
            "retrieved_docs": [],
            "planned_tools": [],
            "tool_results": [],
            "draft_answer": None,
            "final_answer": None,
            "step": 0,
            "errors": [],
            "node_name": "start",
            "event_id": 0,
        }

        self._event_id = 0
        self.loop_guard.reset()

        try:
            # Node 1: classify
            yield await self._emit("node_start", run_id, {"node": "classify_task"})
            state = await self._classify_task(state)
            yield await self._emit("node_end", run_id, {"node": "classify_task", "task_type": state.get("task_type")})

            # Node 2: retrieve
            yield await self._emit("node_start", run_id, {"node": "retrieve_context"})
            state = await self._retrieve_context(state)
            yield await self._emit("node_end", run_id, {"node": "retrieve_context", "docs_found": len(state.get("retrieved_docs", []))})

            # Node 3: plan
            yield await self._emit("node_start", run_id, {"node": "plan_tool_calls"})
            state = await self._plan_tool_calls(state)
            yield await self._emit("node_end", run_id, {"node": "plan_tool_calls", "planned_tools": state.get("planned_tools", [])})

            # Node 4: execute tools (if needed)
            if state.get("planned_tools"):
                yield await self._emit("node_start", run_id, {"node": "execute_tools"})
                state = await self._execute_tools(state)
                yield await self._emit("node_end", run_id, {"node": "execute_tools", "tool_results_count": len(state.get("tool_results", []))})

            # Node 5: generate answer
            yield await self._emit("node_start", run_id, {"node": "generate_answer"})
            async for event in self._generate_answer(state):
                yield event
            yield await self._emit("node_end", run_id, {"node": "generate_answer"})

            # Node 6: verify
            yield await self._emit("node_start", run_id, {"node": "verify_answer"})
            state = await self._verify_answer(state)
            yield await self._emit("node_end", run_id, {"node": "verify_answer", "verified": state.get("final_answer") is not None})

            yield await self._emit("done", run_id, {"final_answer": state.get("final_answer", "")})

        except Exception as e:
            logger.error("Agent %s error: %s", run_id, e)
            yield await self._emit("error", run_id, {"message": str(e)})

    async def _classify_task(self, state: AgentState) -> AgentState:
        state["step"] += 1
        fault = self.loop_guard.check_step()
        if fault:
            state["errors"].append({"node": "classify", "error": fault.message})
            return state

        goal = state["goal"].lower()
        if any(w in goal for w in ["search", "find", "retrieve", "look up", "research"]):
            state["task_type"] = "retrieval"
        elif any(w in goal for w in ["calculate", "compute", "math", "solve"]):
            state["task_type"] = "computation"
        elif any(w in goal for w in ["summarize", "summary", "explain"]):
            state["task_type"] = "summarization"
        else:
            state["task_type"] = "general"
        return state

    async def _retrieve_context(self, state: AgentState) -> AgentState:
        state["step"] += 1
        fault = self.loop_guard.check_step()
        if fault:
            state["errors"].append({"node": "retrieve", "error": fault.message})
            return state

        if state.get("task_type") not in ("retrieval", "summarization", "general"):
            return state

        hits = await self.retriever.search(state["goal"], top_k=5)
        reranked = await self.reranker.rerank(state["goal"], hits, top_k=3)
        state["retrieved_docs"] = [
            {"doc_id": h.doc_id, "content": h.content[:500], "score": h.rerank_score}
            for h in reranked
        ]
        return state

    async def _plan_tool_calls(self, state: AgentState) -> AgentState:
        state["step"] += 1
        fault = self.loop_guard.check_step()
        if fault:
            state["errors"].append({"node": "plan", "error": fault.message})
            return state

        tools = await self.tool_registry.list_tools()
        tool_names = [t["name"] for t in tools]

        if state.get("task_type") == "computation":
            state["planned_tools"] = ["calculator"]
        elif state.get("task_type") in ("retrieval", "general"):
            if state["retrieved_docs"]:
                state["planned_tools"] = []
            else:
                state["planned_tools"] = ["web_search"]
        else:
            state["planned_tools"] = []
        return state

    async def _execute_tools(self, state: AgentState) -> AsyncIterator[dict]:
        state["step"] += 1
        for tool_name in state.get("planned_tools", []):
            fault = self.loop_guard.check_tool_call(tool_name)
            if fault:
                state["errors"].append({"node": "execute", "tool": tool_name, "error": fault.message})
                continue

            yield await self._emit("tool_start", state["run_id"], {"tool": tool_name})
            payload = {}
            if tool_name == "calculator":
                payload["expression"] = "2 + 2"
            elif tool_name == "web_search":
                payload["query"] = state["goal"]

            result = await self.tool_registry.execute(tool_name, payload)
            state["tool_results"].append({"tool": tool_name, "result": result})
            yield await self._emit("tool_end", state["run_id"], {"tool": tool_name, "result": result})

    async def _generate_answer(self, state: AgentState) -> AsyncIterator[dict]:
        state["step"] += 1
        fault = self.loop_guard.check_llm_call()
        if fault:
            state["errors"].append({"node": "generate", "error": fault.message})
            yield await self._emit("warning", state["run_id"], {"message": fault.message})
            return

        context = "\n".join(
            d.get("content", "") for d in state.get("retrieved_docs", [])
        )
        tool_info = "\n".join(
            str(r) for r in state.get("tool_results", [])
        )

        prompt = f"Goal: {state['goal']}\n\n"
        if context:
            prompt += f"Context:\n{context}\n\n"
        if tool_info:
            prompt += f"Tool Results:\n{tool_info}\n\n"
        prompt += "Provide a clear, concise answer:"

        full_text = ""
        messages = [{"role": "user", "content": prompt}]

        async for gen in self.gateway_model._astream(messages):
            from langchain_core.messages import AIMessage

            token = gen.content if isinstance(gen, AIMessage) else str(gen)
            full_text += token
            yield await self._emit("token", state["run_id"], {"delta": token})

        state["draft_answer"] = full_text

    async def _verify_answer(self, state: AgentState) -> AgentState:
        state["step"] += 1
        draft = state.get("draft_answer", "")
        if not draft or len(draft) < 10:
            state["final_answer"] = "I was unable to generate a sufficient answer."
            state["errors"].append({"node": "verify", "error": "answer too short"})
        else:
            state["final_answer"] = draft.strip()
        return state

    async def _emit(self, event_type: str, run_id: str, data: dict) -> dict:
        self._event_id += 1
        return {
            "type": event_type,
            "run_id": run_id,
            "event_id": self._event_id,
            "created_at": int(time.time()),
            **data,
        }
