from __future__ import annotations

import math
import time
from typing import Dict, List

from .world import WorldState


def evaluate_trade_position(world: WorldState, country: str) -> Dict[str, float]:
    state = world.countries[country]
    trade_balance = sum(state.exports.values()) - sum(state.imports.values())
    exposure = sum(state.imports.values())
    return {
        "trade_balance": round(trade_balance, 2),
        "import_exposure": round(exposure, 2),
        "average_tariff": round(sum(state.tariffs.values()) / len(state.tariffs), 3),
    }


def calculate_tariff_impact(
    world: WorldState, country: str, target_good: str, rate: float
) -> Dict[str, float]:
    state = world.countries[country]
    import_volume = state.imports.get(target_good, 0.0)
    consumer_loss = -(import_volume * rate)
    producer_gain = import_volume * rate * 0.5
    government_revenue = import_volume * rate * 0.7
    deadweight_loss = consumer_loss - producer_gain - government_revenue
    return {
        "consumer_surplus_change": round(consumer_loss, 2),
        "producer_surplus_change": round(producer_gain, 2),
        "government_revenue": round(government_revenue, 2),
        "deadweight_loss": round(deadweight_loss, 2),
    }


def propose_policy_action(action_type: str, params: Dict[str, float]) -> Dict[str, float]:
    return {"action_type": action_type, "parameters": params}


def assess_retaliation_risk(rate: float) -> Dict[str, float]:
    return {"retaliation_risk": round(min(1.0, 0.4 + rate * 1.2), 2)}


def monitor_trade_flows(world: WorldState, country_pair: List[str]) -> Dict[str, float]:
    return {
        "pair": f"{country_pair[0]}-{country_pair[1]}",
        "trade_flow": world.trade_flow,
    }


def detect_policy_changes(events: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [event for event in events if event.get("topic") == "policy"]


def analyze_supply_chains(world: WorldState, sector: str) -> Dict[str, float]:
    return {
        "sector": sector,
        "stress_index": round(0.35 + world.trade_flow.get(sector, 1.0) / 20, 2),
    }


def predict_market_impact(policy: Dict[str, float]) -> Dict[str, float]:
    rate = policy.get("rate", 0.0)
    return {
        "inflation_risk": round(min(1.0, 0.2 + rate * 2.4), 2),
        "equity_drawdown": round(min(1.0, 0.1 + rate * 1.6), 2),
    }


def model_game_structure(scenario: str) -> Dict[str, str]:
    return {"scenario": scenario, "structure": "Repeated Game" if "repeat" in scenario else "Prisoner's Dilemma"}


def find_nash_equilibrium(players: List[str], strategies: Dict[str, List[str]]) -> Dict[str, str]:
    return {"equilibrium": "mutual_deescalation", "players": ",".join(players)}


def predict_response(action: str, opponent: str) -> Dict[str, str]:
    return {"opponent": opponent, "likely_response": "proportional_retaliation" if "tariff" in action else "wait"}


def calculate_payoff_matrix() -> Dict[str, Dict[str, float]]:
    return {
        "Cooperate": {"Cooperate": 3.0, "Defect": 1.0},
        "Defect": {"Cooperate": 4.0, "Defect": 2.0},
    }


def detect_negotiation_window(welfare_losses: Dict[str, float]) -> bool:
    return min(welfare_losses.values()) < 95.0


def generate_deal_proposal(countries: List[str], issues: List[str]) -> Dict[str, object]:
    return {
        "countries": countries,
        "issues": issues,
        "rollback_schedule": ["30% immediate", "40% after review", "30% after 90 days"],
    }


def evaluate_concession_value(offer: Dict[str, object]) -> Dict[str, float]:
    return {"value_score": 0.62, "risk_score": 0.38}


def manage_bargaining_round(offers: List[Dict[str, object]]) -> Dict[str, object]:
    return {"round_status": "counter", "offers": offers[:2]}


def execute_simulation_round(world: WorldState) -> Dict[str, float]:
    gravity_trade_flow(world)
    welfare = world.compute_welfare()
    return welfare


def generate_welfare_report(countries: Dict[str, float]) -> Dict[str, float]:
    return {country: round(value, 2) for country, value in countries.items()}


def detect_equilibrium(state: Dict[str, float]) -> bool:
    return max(state.values()) - min(state.values()) < 1.5


def trigger_event(event_type: str) -> Dict[str, str]:
    return {"event_type": event_type, "status": "triggered"}


def gravity_trade_flow(world: WorldState) -> Dict[str, float]:
    total_gdp = sum(state.gdp for state in world.countries.values())
    tariff_effect = sum(sum(state.tariffs.values()) for state in world.countries.values())
    now = time.time()
    for sector in world.trade_flow:
        baseline = (total_gdp / 1000.0) * 0.8
        sector_bias = 1.0 + (0.02 * (len(sector) % 3))
        wave = 1.0 + 0.06 * math.sin(now / 6 + len(sector))
        world.trade_flow[sector] = round(
            max(0.5, baseline * (1.0 - tariff_effect * 0.01) * sector_bias * wave), 2
        )
    return world.trade_flow
