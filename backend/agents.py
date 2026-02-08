from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .bus import EventBus
from .llm import LLMClient
from .models import Event
from .tools import (
    analyze_supply_chains,
    assess_retaliation_risk,
    calculate_payoff_matrix,
    calculate_tariff_impact,
    detect_negotiation_window,
    detect_policy_changes,
    detect_equilibrium,
    evaluate_concession_value,
    evaluate_trade_position,
    execute_simulation_round,
    find_nash_equilibrium,
    generate_deal_proposal,
    generate_welfare_report,
    manage_bargaining_round,
    model_game_structure,
    monitor_trade_flows,
    predict_market_impact,
    predict_response,
    propose_policy_action,
    trigger_event,
)
from .world import WorldState
from .time_utils import now_ist


def utc_now() -> str:
    return now_ist()


@dataclass
class AgentContext:
    name: str
    status: str = "idle"
    last_action: str = ""
    memory: List[Dict[str, Any]] = field(default_factory=list)


class BaseAgent:
    def __init__(self, name: str, bus: EventBus, world: WorldState, llm: LLMClient) -> None:
        self.name = name
        self.bus = bus
        self.world = world
        self.llm = llm
        self.context = AgentContext(name=name)
        self.subscriptions: List[asyncio.Queue[Event]] = []

    def subscribe(self, topics: List[str]) -> None:
        for topic in topics:
            self.subscriptions.append(self.bus.subscribe(topic))

    def register_tools(self) -> List[str]:
        return []

    def _event(self, topic: str, title: str, memo: str, payload: Dict[str, Any]) -> Event:
        return Event(
            timestamp=utc_now(),
            topic=topic,
            source=self.name,
            title=title,
            memo=memo,
            payload=payload,
        )

    async def on_event(self, event: Event) -> None:
        self.context.memory.append(
            {
                "timestamp": event.timestamp,
                "source": event.source,
                "topic": event.topic,
                "title": event.title,
                "memo": event.memo,
            }
        )
        if len(self.context.memory) > 12:
            self.context.memory = self.context.memory[-12:]

    async def reason_and_act(self, observation: str) -> List[Event]:
        self.context.status = "working"
        tools = self.register_tools()
        tool_results: Dict[str, Any] = {}

        def tool_executor(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
            result = self.execute_tool(name, args)
            tool_results[name] = result
            return result

        loop = asyncio.get_running_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None, lambda: self.llm.reason(self.name, observation, tools, tool_executor)
                ),
                timeout=6.0,
            )
        except asyncio.TimeoutError:
            result = self.llm.heuristic_reason(self.name, observation, tools)
        thoughts = result.thoughts
        memo = result.memo
        events = [
            self._event(
                topic="thought",
                title="Internal memo",
                memo=" | ".join(thoughts),
                payload={"mode": result.mode, "tools": tools},
            )
        ]
        events.extend(self.build_actions(tool_results, memo))
        self.context.status = "idle"
        return events

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "evaluate_trade_position":
            return evaluate_trade_position(self.world, args["country"])
        if name == "calculate_tariff_impact":
            return calculate_tariff_impact(
                self.world, args["country"], args["target_good"], args["rate"]
            )
        if name == "propose_policy_action":
            return propose_policy_action(args["action_type"], args["parameters"])
        if name == "assess_retaliation_risk":
            return assess_retaliation_risk(args["rate"])
        if name == "monitor_trade_flows":
            return monitor_trade_flows(self.world, args["country_pair"])
        if name == "detect_policy_changes":
            recent_events = [event.__dict__ for event in self.bus.recent(50)]
            return {"changes": detect_policy_changes(recent_events)}
        if name == "analyze_supply_chains":
            return analyze_supply_chains(self.world, args["sector"])
        if name == "predict_market_impact":
            return predict_market_impact(args["policy"])
        if name == "model_game_structure":
            return model_game_structure(args["scenario"])
        if name == "find_nash_equilibrium":
            return find_nash_equilibrium(args["players"], args["strategies"])
        if name == "predict_response":
            return predict_response(args["action"], args["opponent"])
        if name == "calculate_payoff_matrix":
            return calculate_payoff_matrix()
        if name == "detect_negotiation_window":
            welfare_losses = args.get("welfare_losses") or self.world.compute_welfare()
            return {"window": detect_negotiation_window(welfare_losses)}
        if name == "generate_deal_proposal":
            return generate_deal_proposal(args["countries"], args["issues"])
        if name == "evaluate_concession_value":
            return evaluate_concession_value(args["offer"])
        if name == "manage_bargaining_round":
            return manage_bargaining_round(args["offers"])
        if name == "execute_simulation_round":
            return execute_simulation_round(self.world)
        if name == "generate_welfare_report":
            return generate_welfare_report(args["countries"])
        if name == "detect_equilibrium":
            return {"equilibrium": detect_equilibrium(args["state"])}
        if name == "trigger_event":
            return trigger_event(args["event_type"])
        return {}

    def build_actions(self, tool_results: Dict[str, Any], memo: str) -> List[Event]:
        return []

    async def run(self) -> None:
        while True:
            for queue in list(self.subscriptions):
                try:
                    event = queue.get_nowait()
                except asyncio.QueueEmpty:
                    continue
                await self.on_event(event)
            observation = (
                f"Recent events: {self.context.memory[-3:]}\n"
                f"Welfare snapshot: {self.world.compute_welfare()}\n"
                f"Tariffs: {{"
                + ", ".join(
                    f"{name}: {state.tariffs}" for name, state in self.world.countries.items()
                )
                + "}"
            )
            events = await self.reason_and_act(observation)
            for event in events:
                await self.bus.publish(event)
            await asyncio.sleep(1.6)


class CountryStrategyAgent(BaseAgent):
    def __init__(self, name: str, country: str, *args: Any, learning: bool = False) -> None:
        super().__init__(name, *args)
        self.country = country
        self.learning = learning
        self.aggression = 0.55 if learning else 0.45
        self.last_welfare = 100.0
        self.effectiveness_score = 0.0
        self.subscribe(["policy", "market", "strategy", "negotiation"])

    def register_tools(self) -> List[str]:
        return [
            "evaluate_trade_position",
            "calculate_tariff_impact",
            "propose_policy_action",
            "assess_retaliation_risk",
        ]

    def build_actions(self, tool_results: Dict[str, Any], memo: str) -> List[Event]:
        state = self.world.countries[self.country]
        current = state.tariffs.get("electronics", 0.08)
        risk = tool_results.get("assess_retaliation_risk", {}).get("retaliation_risk", 0.5)
        strategy_bias = any(
            "de-escalation" in entry.get("memo", "").lower() for entry in self.context.memory[-5:]
        )
        if risk > 0.75:
            new_rate = max(0.05, current - 0.02)
            action = "partial_rollback"
        else:
            increment = 0.02 if strategy_bias else 0.03
            new_rate = min(0.5, current + increment + (self.aggression * 0.02))
            action = "tariff_increase"
        if action == self.context.last_action:
            memo = memo + " Override executed to avoid policy inertia."
        self.context.last_action = action
        state.tariffs["electronics"] = new_rate
        if self.learning:
            welfare = self.world.compute_welfare().get(self.country, 100.0)
            delta = welfare - self.last_welfare
            self.effectiveness_score = (self.effectiveness_score * 0.7) + (delta * 0.3)
            if delta > 0:
                self.aggression = min(0.85, self.aggression + 0.03)
            else:
                self.aggression = max(0.2, self.aggression - 0.04)
            self.last_welfare = welfare
        return [
            self._event(
                topic="policy",
                title=f"{self.country} policy update",
                memo=memo,
                payload={
                    "action": action,
                    "sector": "electronics",
                    "rate": round(new_rate, 3),
                    "aggression": round(self.aggression, 2),
                    "effectiveness_score": round(self.effectiveness_score, 2),
                },
            )
        ]


class MarketIntelligenceAgent(BaseAgent):
    def __init__(self, *args: Any) -> None:
        super().__init__("Market Intelligence Agent", *args)
        self.subscribe(["policy", "scenario"])

    def register_tools(self) -> List[str]:
        return [
            "monitor_trade_flows",
            "detect_policy_changes",
            "analyze_supply_chains",
            "predict_market_impact",
        ]

    def build_actions(self, tool_results: Dict[str, Any], memo: str) -> List[Event]:
        memo = (
            "Electronics sector experiencing compounding tariff shock; downstream inflation risk rising."
        )
        payload = {
            "trade_flow": self.world.trade_flow,
            "market_impact": tool_results.get("predict_market_impact", {}),
            "supply_chain": tool_results.get("analyze_supply_chains", {}),
        }
        return [self._event("market", "Sector exposure update", memo, payload)]


class GameTheoryAgent(BaseAgent):
    def __init__(self, *args: Any) -> None:
        super().__init__("Game Theory & Strategy Agent", *args)
        self.subscribe(["policy", "scenario"])

    def register_tools(self) -> List[str]:
        return [
            "model_game_structure",
            "find_nash_equilibrium",
            "predict_response",
            "calculate_payoff_matrix",
        ]

    def build_actions(self, tool_results: Dict[str, Any], memo: str) -> List[Event]:
        memo = (
            "Scenario classified as Repeated Game; escalation risk elevated. "
            "Recommend calibrated de-escalation with conditional rollback."
        )
        payload = {
            "classification": "Repeated Game",
            "payoff_matrix": tool_results.get("calculate_payoff_matrix", {}),
            "equilibrium": tool_results.get("find_nash_equilibrium", {}),
        }
        return [self._event("strategy", "Strategic classification", memo, payload)]


class NegotiationAgent(BaseAgent):
    def __init__(self, *args: Any) -> None:
        super().__init__("Negotiation & Resolution Agent", *args)
        self.subscribe(["policy", "strategy", "scenario"])

    def register_tools(self) -> List[str]:
        return [
            "detect_negotiation_window",
            "generate_deal_proposal",
            "evaluate_concession_value",
            "manage_bargaining_round",
        ]

    def build_actions(self, tool_results: Dict[str, Any], memo: str) -> List[Event]:
        if tool_results.get("detect_negotiation_window", {}).get("window"):
            memo = (
                "ZOPA detected. Propose phased rollback: 30% immediate, 40% after review, "
                "30% after 90-day stability window."
            )
            payload = {"proposal": tool_results.get("generate_deal_proposal", {})}
            return [self._event("negotiation", "Negotiation window opened", memo, payload)]
        memo = "No credible ZOPA; hold position while signaling limited rollback capacity."
        return [self._event("negotiation", "Negotiation assessment", memo, {})]
