# Trade Conflict Simulation Console

Research-grade prototype for an autonomous multi-agent trade war simulation with an institutional dashboard and agentic coordination.

## Run

```powershell
pip install -r requirements.txt
setx OPENAI_API_KEY "your_key"
python backend\run.py
```

Open `http://127.0.0.1:8000` in a browser.

## Architecture (5-minute explanation)

- `backend/system.py` boots the world state, agents, and shared-state publisher.
- `backend/agents.py` contains autonomous agents with OpenAI tool-calling loops and internal memos.
- `backend/scenario_agent.py` is the Scenario Execution Agent that advances phases and rounds.
- `backend/bus.py` is a pub-sub bus used by agents to coordinate peer-to-peer.
- `dashboard/` renders a policy-grade console and polls the shared state on a fixed cadence.

## Notes

- All agent reasoning is expressed as policy notes / internal memos.
- Country Alpha uses in-system learning to adapt aggression based on welfare deltas.
- Set `REDIS_URL` to enable Redis-backed shared state.
- Set `OPENAI_MODEL` to override the default model (`gpt-4o-mini`).
- For OpenRouter: set `LLM_PROVIDER=openrouter`, `OPENROUTER_API_KEY`, and `OPENROUTER_MODEL` (e.g. `anthropic/claude-3.5-sonnet`).
