from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from .agents import BaseAgent
from .models import Event
from .time_utils import now_ist


def utc_now() -> str:
    return now_ist()


PHASES = [
    "Cold Start",
    "Initial Shock",
    "Escalation",
    "Strategic Adaptation",
    "Negotiation or Collapse",
    "Learning Update",
]


class ScenarioExecutionAgent(BaseAgent):
    def __init__(self, *args: Any) -> None:
        super().__init__("Scenario Execution Agent", *args)
        self.round_id = 1
        self.phase_index = 0
        self.subscribe(["policy", "market", "strategy", "negotiation"])

    def register_tools(self) -> List[str]:
        return [
            "execute_simulation_round",
            "generate_welfare_report",
            "detect_equilibrium",
            "trigger_event",
        ]

    def build_actions(self, tool_results: Dict[str, Any], memo: str) -> List[Event]:
        phase = PHASES[self.phase_index]
        memo = "Phase transition executed; monitoring welfare deltas and escalation thresholds."
        payload = {
            "round": self.round_id,
            "phase": phase,
            "welfare": tool_results.get("generate_welfare_report", {}),
            "equilibrium": tool_results.get("detect_equilibrium", {}).get("equilibrium", False),
        }
        events = [self._event("scenario", "Phase update", memo, payload)]
        self.phase_index = (self.phase_index + 1) % len(PHASES)
        if self.phase_index == 0:
            self.round_id += 1
        return events

    async def run(self) -> None:
        while True:
            observation = f"Phase {PHASES[self.phase_index]} | round {self.round_id}"
            events = await self.reason_and_act(observation)
            for event in events:
                await self.bus.publish(event)
            await asyncio.sleep(1.2)
