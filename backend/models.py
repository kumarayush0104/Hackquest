from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .world import CountryState


@dataclass
class Event:
    timestamp: str
    topic: str
    source: str
    title: str
    memo: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationState:
    round_id: int
    phase: str
    classification: str
    learning_metrics: Dict[str, Any]
    trade_flow: Dict[str, float]
    welfare_impact: Dict[str, float]
    policy_timeline: List[Dict[str, Any]]
    agents: Dict[str, Any]
