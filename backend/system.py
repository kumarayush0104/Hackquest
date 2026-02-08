from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Dict

from .agents import (
    CountryStrategyAgent,
    GameTheoryAgent,
    MarketIntelligenceAgent,
    NegotiationAgent,
)
from .bus import EventBus
from .llm import LLMClient
from .models import Event
from .scenario_agent import ScenarioExecutionAgent
from .storage import SharedStateStore
from .world import CountryState, SECTORS, WorldState
from .tools import gravity_trade_flow
from .time_utils import now_ist


ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "shared"


def build_world() -> WorldState:
    def sector_map(base: float) -> Dict[str, float]:
        return {sector: round(base * factor, 2) for sector, factor in zip(SECTORS, [1.2, 1.0, 0.8, 0.7, 0.9])}

    countries = {
        "Country Alpha": CountryState(
            name="Country Alpha",
            gdp=2100.0,
            exports=sector_map(180.0),
            imports=sector_map(140.0),
            tariffs={sector: 0.08 for sector in SECTORS},
            political_pressure=0.6,
            strategic_posture="Export defense",
        ),
        "Country Beta": CountryState(
            name="Country Beta",
            gdp=1800.0,
            exports=sector_map(140.0),
            imports=sector_map(170.0),
            tariffs={sector: 0.06 for sector in SECTORS},
            political_pressure=0.55,
            strategic_posture="Import security",
        ),
        "Country Gamma": CountryState(
            name="Country Gamma",
            gdp=1500.0,
            exports=sector_map(120.0),
            imports=sector_map(110.0),
            tariffs={sector: 0.05 for sector in SECTORS},
            political_pressure=0.48,
            strategic_posture="Coalition hedge",
        ),
    }
    trade_flow = {sector: 8.0 for sector in SECTORS}
    return WorldState(countries=countries, trade_flow=trade_flow)


def serialize_events(events: list[Event]) -> list[dict[str, object]]:
    return [
        {
            "timestamp": event.timestamp,
            "source": event.source,
            "title": event.title,
            "memo": event.memo,
            "topic": event.topic,
            "payload": event.payload,
        }
        for event in events
    ]


async def state_publisher(bus: EventBus, world: WorldState, store: SharedStateStore, agents: list) -> None:
    while True:
        gravity_trade_flow(world)
        world.apply_sector_drift()
        welfare = world.compute_welfare()
        for name, value in welfare.items():
            world.countries[name].welfare = value
        alpha_agent = next(
            (agent for agent in agents if agent.context.name == "Country Strategy Agent (Alpha)"),
            None,
        )
        learning_payload = {
            "alpha_aggression": getattr(alpha_agent, "aggression", 0.0),
            "effectiveness_score": getattr(alpha_agent, "effectiveness_score", 0.0),
            "note": "Policy effectiveness improving over simulations"
            if getattr(alpha_agent, "effectiveness_score", 0.0) > 0
            else "Policy effectiveness deteriorating; de-escalation bias increased.",
        }
        timeline = []
        for event in bus.recent(20):
            if event.topic in {"scenario", "policy", "negotiation"}:
                timeline.append({"timestamp": event.timestamp, "label": event.title})
        recent_events = bus.recent(60)
        payload = {
            "timestamp": now_ist(),
            "phase": next(
                (
                    event.payload.get("phase")
                    for event in reversed(recent_events)
                    if event.topic == "scenario"
                ),
                "Cold Start",
            ),
            "round": next(
                (
                    event.payload.get("round")
                    for event in reversed(recent_events)
                    if event.topic == "scenario"
                ),
                1,
            ),
            "classification": next(
                (
                    event.payload.get("classification")
                    for event in reversed(recent_events)
                    if event.topic == "strategy"
                ),
                "Repeated Game",
            ),
            "learning": learning_payload,
            "countries": {
                name: {
                    "gdp": state.gdp,
                    "exports": state.exports,
                    "imports": state.imports,
                    "tariffs": state.tariffs,
                    "welfare": state.welfare,
                    "political_pressure": state.political_pressure,
                    "strategic_posture": state.strategic_posture,
                }
                for name, state in world.countries.items()
            },
            "trade_flow": world.trade_flow,
            "welfare_impact": welfare,
            "events": serialize_events(recent_events),
            "policy_timeline": timeline[-12:],
            "agent_status": {agent.context.name: agent.context.status for agent in agents},
            "system_health": {"backend": store.backend},
        }
        store.write("state", payload)
        store.write("events", payload.get("events", []))
        await asyncio.sleep(1.0)


async def run_system() -> None:
    bus = EventBus()
    world = build_world()
    llm = LLMClient()
    store = SharedStateStore(SHARED_DIR, os.getenv("REDIS_URL"))

    agents = [
        CountryStrategyAgent(
            "Country Strategy Agent (Alpha)", "Country Alpha", bus, world, llm, learning=True
        ),
        CountryStrategyAgent("Country Strategy Agent (Beta)", "Country Beta", bus, world, llm),
        CountryStrategyAgent("Country Strategy Agent (Gamma)", "Country Gamma", bus, world, llm),
        MarketIntelligenceAgent(bus, world, llm),
        GameTheoryAgent(bus, world, llm),
        NegotiationAgent(bus, world, llm),
        ScenarioExecutionAgent(bus, world, llm),
    ]

    tasks = [asyncio.create_task(agent.run()) for agent in agents]
    tasks.append(asyncio.create_task(state_publisher(bus, world, store, agents)))
    await asyncio.gather(*tasks)
