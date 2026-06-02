# autoppia_web_agent_example (Template)

This repository is a **reference implementation** for Autoppia web-agent miners.

## Purpose

Use this repo to understand the minimum API contract expected by the subnet validator:

- `main.py` must export `app`
- `GET /health` must return HTTP 200
- `POST /find_trayectory` must return JSON with top-level `trajectory` list
- `POST /act` and `POST /step` remain as legacy/simple endpoints

## Current behavior

`POST /find_trayectory` invokes Claude Code and returns:

```json
{
  "web_agent_id": "autoppia-web-agent-example",
  "trajectory": [
    {"name": "browser.navigate", "arguments": {"url": "https://example.com"}}
  ]
}
```

`POST /act` still returns `{"actions": []}` for legacy shape checks.

## Entry point

Validator-compatible run command:

```bash
uvicorn main:app --host 0.0.0.0 --port $SANDBOX_AGENT_PORT
```

## Example `/find_trayectory` request shape

```json
{
  "id": "example-task-id",
  "prompt": "Do something on the webpage",
  "url": "https://example.com",
  "web_project_id": "autocinema"
}
```

## Included tools for miners

These are generic and reusable helpers, not agent logic:

- `llm_gateway.py`
  - OpenAI-compatible gateway helper
  - Adds required `IWA-Task-ID` header
  - Reads `OPENAI_BASE_URL` so miners can route through sandbox gateway
- `claude_code_provider.py`
  - Claude Code CLI adapter for `/find_trayectory`
  - Reads `CLAUDE_CODE_BIN`, `CLAUDE_CODE_MODEL`, `CLAUDE_CODE_TIMEOUT_SECONDS`, and optional `CLAUDE_CODE_MAX_BUDGET_USD`
  - Requires Claude Code CLI on `PATH` and either `ANTHROPIC_API_KEY` or existing Claude auth
- `eval.py`
  - Generic `/act` evaluator (shape + status + latency)
  - Works with default synthetic tasks or a JSON tasks file
- `compare_eval.py`
  - Runs `eval.py` across multiple `provider:model` configs and aggregates results

## Quick usage

Run template server:

```bash
uvicorn main:app --host 0.0.0.0 --port 5000
```

Call `/find_trayectory`:

```bash
curl -sS http://127.0.0.1:5000/find_trayectory \
  -H 'Content-Type: application/json' \
  -d '{"id":"t1","prompt":"Open the homepage","url":"https://example.com"}'
```

Run generic eval:

```bash
python eval.py --agent-base-url http://127.0.0.1:5000 --num-tasks 5
```

Run compare tool:

```bash
python compare_eval.py --runs openai:gpt-5.2 openai:gpt-4o-mini --agent-base-url http://127.0.0.1:5000 --num-tasks 5
```

## Notes for miners

- Start from this template and add your own logic incrementally.
- Keep the new response shape stable: `{ "trajectory": [...] }`.
- Each trajectory item should be a tool call: `{ "name": "browser.click", "arguments": {...} }`.
- Claude Code is a CLI dependency, not a Python package. In Docker, install/provide `claude`; in local dev, run `claude auth` or set `ANTHROPIC_API_KEY`.
- Optionally keep `/step` as an alias for `/act` for older validators.
