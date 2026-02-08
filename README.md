# Trade Conflict Simulation Console

A multi-agent trade conflict simulator with a live policy dashboard.

This project runs a continuous simulation where autonomous agents represent country strategy, market intelligence, game-theory analysis, negotiation, and scenario control. Agents publish structured events to an internal bus, and a shared state snapshot is rendered in a browser dashboard.

## What this project does

- Simulates tariff escalation dynamics across 3 countries and 5 sectors.
- Runs multiple specialized agents concurrently with tool-driven reasoning loops.
- Produces live outputs (`shared/state.json`, `shared/events.json`) for visualization.
- Shows phase progression, policy timeline, learning metrics, welfare impact, and agent feeds.

## Core features

- **Autonomous agent system**
  - 3 country strategy agents (Alpha, Beta, Gamma)
  - Market Intelligence Agent
  - Game Theory & Strategy Agent
  - Negotiation & Resolution Agent
  - Scenario Execution Agent
- **State evolution model**
  - Gravity-style trade flow updates
  - Tariff drag and sector drift
  - Country welfare scoring
- **Learning loop (Country Alpha)**
  - Adaptive aggression tuning based on welfare delta
  - Rolling policy effectiveness score
- **Live dashboard (no frontend build step)**
  - Policy timeline and event feed
  - Trade flow chart + sector heatmap
  - Welfare trend line chart
  - Country-level GDP / welfare / pressure / imports / exports / tariffs

## Repository structure

```text
backend/
  run.py                # Starts simulation + HTTP server
  system.py             # World bootstrap, agents, publisher loop
  agents.py             # BaseAgent + specialized agents
  scenario_agent.py     # Round/phase progression agent
  world.py              # Core world and welfare model
  tools.py              # Domain tool functions used by agents
  tool_schemas.py       # Tool schemas for LLM function-calling
  llm.py                # OpenAI/OpenRouter + heuristic fallback
  bus.py                # In-memory pub/sub event bus
  storage.py            # Shared state persistence (file/redis)
  models.py             # Event / simulation dataclasses
  time_utils.py         # IST timestamp utility

dashboard/
  index.html            # Dashboard layout
  app.js                # Polling, rendering, chart drawing
  styles.css            # Visual system

shared/
  state.json            # Latest simulation snapshot
  events.json           # Latest event list
```

## How it works

1. `backend/run.py` starts:
   - an HTTP server at `127.0.0.1:8000`
   - the simulation runtime (`run_system`) concurrently
2. `backend/system.py` initializes world state and all agents.
3. Agents publish events to `EventBus` (`backend/bus.py`).
4. `state_publisher` composes a dashboard payload every second and writes it to shared storage.
5. `dashboard/app.js` polls `/shared/state.json` every ~1.2s and updates UI panels.

## Quick start

### Prerequisites

- Python 3.10+ (3.12 recommended)
- `pip`
- Optional: Redis (only if you want Redis-backed storage)

### 1) Install dependencies

```powershell
pip install -r requirements.txt
```

### 2) Configure environment (optional)

Default behavior works without API keys (heuristic mode).

For OpenAI mode:

```powershell
$env:LLM_PROVIDER="openai"
$env:OPENAI_API_KEY="your_openai_key"
$env:OPENAI_MODEL="gpt-4o-mini"   # optional override
```

For OpenRouter mode:

```powershell
$env:LLM_PROVIDER="openrouter"
$env:OPENROUTER_API_KEY="your_openrouter_key"
$env:OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"  # example
```

### 3) Run

```powershell
python backend\run.py
```

### 4) Open dashboard

- `http://127.0.0.1:8000`

## LLM execution modes

`backend/llm.py` resolves runtime mode as:

- `openai`: if `LLM_PROVIDER=openai` and `OPENAI_API_KEY` is set
- `openrouter`: if `LLM_PROVIDER=openrouter` and `OPENROUTER_API_KEY` is set
- `heuristic`: fallback if credentials/provider are unavailable

If tool-calling times out in agent reasoning, the agent falls back to heuristic logic for that cycle.

## Simulation model details

### Countries and sectors

Initial countries:

- Country Alpha (export-defense posture)
- Country Beta (import-security posture)
- Country Gamma (coalition-hedge posture)

Sectors:

- electronics
- automotive
- agriculture
- energy
- manufacturing

### Welfare model

Welfare is computed from:

- tariff drag
- import exposure
- export exposure
- aggregate trade-flow factor

See `backend/world.py` (`compute_welfare`).

### Tariff policy behavior

Country strategy agents adjust electronics tariff primarily based on:

- retaliation risk
- recent memory context (de-escalation bias)
- aggression parameter
- policy inertia override checks

Country Alpha additionally updates:

- `aggression`
- `effectiveness_score`

based on welfare deltas.

### Scenario progression

`ScenarioExecutionAgent` cycles phases:

1. Cold Start
2. Initial Shock
3. Escalation
4. Strategic Adaptation
5. Negotiation or Collapse
6. Learning Update

After phase 6, round increments and cycle repeats.

## Dashboard data contract

Main payload: `shared/state.json`

Top-level keys include:

- `timestamp`
- `phase`
- `round`
- `classification`
- `learning`
- `countries`
- `trade_flow`
- `welfare_impact`
- `events`
- `policy_timeline`
- `agent_status`
- `system_health`

The dashboard is intentionally thin: no framework, no build tooling, plain HTML/CSS/JS canvas rendering.

## Configuration reference

| Variable | Purpose | Default |
|---|---|---|
| `LLM_PROVIDER` | LLM backend selector (`openai` / `openrouter`) | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | unset |
| `OPENAI_MODEL` | OpenAI model override | `gpt-4o-mini` |
| `OPENROUTER_API_KEY` | OpenRouter API key | unset |
| `OPENROUTER_MODEL` | OpenRouter model | `gpt-4o-mini` fallback path |
| `REDIS_URL` | Enables Redis in `SharedStateStore` | unset |

## Important note on Redis mode

The current dashboard reads `/shared/state.json` from the local filesystem.

`SharedStateStore` switches to Redis writes when `REDIS_URL` is set, which means file snapshots are not written by default in that mode. If you enable Redis, add a file-mirroring layer (or modify dashboard data access) so the browser still receives state updates.

## Extending the project

### Add a new agent

1. Implement a new subclass in `backend/agents.py` (or new module).
2. Register topic subscriptions.
3. Expose tool names via `register_tools`.
4. Emit structured `Event` objects in `build_actions`.
5. Add the agent instance to `agents` list in `backend/system.py`.

### Add a new tool

1. Implement function in `backend/tools.py`.
2. Add schema in `backend/tool_schemas.py`.
3. Route tool execution in `BaseAgent.execute_tool` (`backend/agents.py`).
4. Include tool name in `register_tools` for relevant agent(s).

## Troubleshooting

### Dashboard loads but stays static

- Confirm `python backend\run.py` is still running.
- Check `shared/state.json` is being updated.
- If using `REDIS_URL`, see the Redis note above.

### Agents appear repetitive

- This can happen in heuristic mode by design.
- Set valid LLM credentials/provider to enable richer tool-calling behavior.

### Port conflict on `8000`

- Another local process may already be using the port.
- Stop that process or change the server bind in `backend/run.py`.

## Current limitations

- No automated test suite yet.
- In-memory event bus is single-process only.
- Redis mode is not wired directly into dashboard reads.
- No authentication or multi-user session model.

## License

No explicit license file is present.
