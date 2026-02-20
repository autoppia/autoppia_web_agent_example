# autoppia_web_agent_example (Template)

This repository is a **format template** for Autoppia web-agent miners.

It is intentionally **not** a real agent implementation.

## Purpose

Use this repo to understand the minimum API contract expected by the subnet validator:

- `main.py` must export `app`
- `GET /health` must return HTTP 200
- `POST /act` must return JSON with top-level `actions` list

## Current behavior

`POST /act` always returns:

```json
{"actions": []}
```

This is by design. It demonstrates the response schema only.

## Entry point

Validator-compatible run command:

```bash
uvicorn main:app --host 0.0.0.0 --port $SANDBOX_AGENT_PORT
```

## Example `/act` request shape

```json
{
  "task_id": "example-task-id",
  "prompt": "Do something on the webpage",
  "url": "https://example.com",
  "snapshot_html": "<html>...</html>",
  "step_index": 0,
  "history": []
}
```

## Included tools for miners

These are generic and reusable helpers, not agent logic:

- `llm_gateway.py`
  - OpenAI-compatible gateway helper
  - Adds required `IWA-Task-ID` header
  - Reads `OPENAI_BASE_URL` so miners can route through sandbox gateway
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
- Keep the response shape stable: `{ "actions": [...] }`.
- Optionally implement `/step` as an alias for `/act`.
