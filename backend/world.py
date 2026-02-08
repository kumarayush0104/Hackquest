from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


SECTORS = ["electronics", "automotive", "agriculture", "energy", "manufacturing"]


@dataclass
class CountryState:
    name: str
    gdp: float
    exports: Dict[str, float]
    imports: Dict[str, float]
    tariffs: Dict[str, float]
    welfare: float = 100.0
    political_pressure: float = 0.5
    strategic_posture: str = "Neutral"


@dataclass
class WorldState:
    countries: Dict[str, CountryState]
    trade_flow: Dict[str, float]
    history: List[Dict[str, float]] = field(default_factory=list)

    def apply_tariff(self, country: str, sector: str, rate: float) -> None:
        self.countries[country].tariffs[sector] = max(0.0, min(0.5, rate))

    def update_trade_flow(self) -> None:
        drag = sum(
            sum(state.tariffs.values()) for state in self.countries.values()
        ) / max(len(self.countries), 1)
        for sector in self.trade_flow:
            self.trade_flow[sector] = round(
                max(0.5, self.trade_flow[sector] * (1.0 - drag * 0.08)), 2
            )

    def apply_sector_drift(self) -> None:
        for state in self.countries.values():
            for sector in state.imports:
                tariff = state.tariffs.get(sector, 0.05)
                state.imports[sector] = round(
                    max(20.0, state.imports[sector] * (1.0 - tariff * 0.01)), 2
                )
            for sector in state.exports:
                tariff = state.tariffs.get(sector, 0.05)
                state.exports[sector] = round(
                    max(20.0, state.exports[sector] * (1.0 - tariff * 0.008)), 2
                )

    def compute_welfare(self) -> Dict[str, float]:
        welfare = {}
        for name, state in self.countries.items():
            tariff_drag = sum(state.tariffs.values()) * 5
            import_exposure = sum(state.imports.values()) / 1000
            export_exposure = sum(state.exports.values()) / 1000
            trade_flow_factor = sum(self.trade_flow.values()) / 100
            welfare[name] = round(
                100.0 - tariff_drag - import_exposure - export_exposure + trade_flow_factor,
                2,
            )
        return welfare
