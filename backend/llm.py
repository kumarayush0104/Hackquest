from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List

from .tool_schemas import schemas

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]
    call_id: str | None = None


@dataclass
class LLMResult:
    thoughts: List[str]
    tool_calls: List[ToolCall]
    memo: str
    mode: str


class LLMClient:
    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv(
            "OPENAI_MODEL",
            os.getenv("OPENROUTER_MODEL", "gpt-4o-mini"),
        )
        self.mode = self._resolve_mode()
        if self.mode == "openai":
            self.client = OpenAI(api_key=self.openai_key)
        elif self.mode == "openrouter":
            self.client = OpenAI(
                api_key=self.openrouter_key, base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.client = None

    def _resolve_mode(self) -> str:
        if self.provider == "openai" and self.openai_key and OpenAI:
            return "openai"
        if self.provider == "openrouter" and self.openrouter_key and OpenAI:
            return "openrouter"
        return "heuristic"

    def reason(
        self,
        agent_name: str,
        observation: str,
        tools: List[str],
        tool_executor,
    ) -> LLMResult:
        if self.mode in {"openai", "openrouter"}:
            return self._openai_reason(agent_name, observation, tools, tool_executor)
        return self._heuristic(agent_name, observation, tools)

    def _openai_reason(
        self, agent_name: str, observation: str, tools: List[str], tool_executor
    ) -> LLMResult:
        system = (
            "You are a senior economic strategist in a trade-war simulation. "
            "Respond with a concise JSON object with keys: policy_notes (array of strings), "
            "decision (string), memo (string). Use formal policy language. "
            "Do not reveal chain-of-thought. Use at least one tool when available."
        )
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f"Agent: {agent_name}\n"
                    f"Observation: {observation}\n"
                    f"Available tools: {tools}"
                ),
            },
        ]

        allowed = [schema for schema in schemas() if schema["name"] in tools]
        tool_calls: List[ToolCall] = []

        for _ in range(3):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=allowed or None,
                tool_choice="required" if allowed else None,
                temperature=0.4,
                response_format={"type": "json_object"},
            )
            message = response.choices[0].message
            if getattr(message, "tool_calls", None):
                tool_outputs = []
                for call in message.tool_calls:
                    name = call.function.name
                    args = json.loads(call.function.arguments or "{}")
                    tool_calls.append(ToolCall(name=name, arguments=args, call_id=call.id))
                    tool_outputs.append((call.id, name, tool_executor(name, args)))
                messages.append(message)
                for call_id, _, result in tool_outputs:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": json.dumps(result),
                        }
                    )
                continue
            content = message.content or "{}"
            try:
                payload = json.loads(content)
            except json.JSONDecodeError:
                payload = {"policy_notes": [], "decision": "hold", "memo": content}
            return LLMResult(
                thoughts=payload.get("policy_notes", []),
                tool_calls=tool_calls,
                memo=payload.get("memo", payload.get("decision", "")),
                mode="openai",
            )

        return LLMResult(
            thoughts=["Timeout in tool loop; reverting to cautious posture."],
            tool_calls=tool_calls,
            memo="Hold position pending additional signals.",
            mode="openai",
        )

    def _heuristic(self, agent_name: str, observation: str, tools: List[str]) -> LLMResult:
        thoughts = [
            f"Observation captured: {observation[:160]}",
            "Assessing welfare risks and political pressure signals.",
        ]
        tool_calls: List[ToolCall] = []
        if "evaluate_trade_position" in tools:
            tool_calls.append(ToolCall("evaluate_trade_position", {"country": "Country Alpha"}))
        if "model_game_structure" in tools:
            tool_calls.append(ToolCall("model_game_structure", {"scenario": "repeat"}))
        memo = (
            "Policy posture adjusted based on risk-weighted welfare outlook. "
            "Maintaining optionality for de-escalation if retaliation accelerates."
        )
        return LLMResult(thoughts=thoughts, tool_calls=tool_calls, memo=memo, mode="heuristic")

    def heuristic_reason(self, agent_name: str, observation: str, tools: List[str]) -> LLMResult:
        return self._heuristic(agent_name, observation, tools)
