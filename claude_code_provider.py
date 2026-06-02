from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
from dataclasses import dataclass
from typing import Any


TRAJECTORY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "confidence": {"type": "number"},
        "summary": {"type": "string"},
        "failure_reason": {"type": "string"},
        "trajectory": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "arguments": {"type": "object"},
                    "reasoning": {"type": "string"},
                },
                "required": ["name", "arguments"],
            },
        },
    },
    "required": ["success", "confidence", "summary", "trajectory"],
}


@dataclass(frozen=True)
class TrajectoryResult:
    trajectory: list[dict[str, Any]]
    success: bool = False
    confidence: float = 0.0
    summary: str = ""
    failure_reason: str = ""
    raw_output: str = ""


def _extract_json_candidate(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty Claude Code output")

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            if isinstance(parsed.get("structured_output"), dict):
                return parsed["structured_output"]
            if isinstance(parsed.get("result"), str):
                return _extract_json_candidate(parsed["result"])
            return parsed
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    if fenced:
        parsed = json.loads(fenced.group(1))
        if isinstance(parsed, dict):
            return parsed

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(raw[start : end + 1])
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("could not parse JSON from Claude Code output")


def _normalize_tool_call(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    name = str(item.get("name") or item.get("action") or "").strip()
    if not name:
        return None

    arguments = item.get("arguments")
    if not isinstance(arguments, dict):
        arguments = item.get("args")
    if not isinstance(arguments, dict):
        arguments = {}

    normalized = {"name": name, "arguments": arguments}
    if isinstance(item.get("reasoning"), str) and item["reasoning"].strip():
        normalized["reasoning"] = item["reasoning"].strip()
    return normalized


def parse_claude_code_output(stdout: str) -> TrajectoryResult:
    parsed = _extract_json_candidate(stdout)

    raw_trajectory = None
    for field in ("trajectory", "tool_calls", "actions"):
        value = parsed.get(field)
        if isinstance(value, list):
            raw_trajectory = value
            break
    raw_trajectory = raw_trajectory or []

    trajectory = [
        tool_call
        for item in raw_trajectory
        for tool_call in [_normalize_tool_call(item)]
        if tool_call is not None
    ]

    return TrajectoryResult(
        success=bool(parsed.get("success")),
        confidence=float(parsed.get("confidence") or 0.0),
        summary=str(parsed.get("summary") or ""),
        failure_reason=str(parsed.get("failure_reason") or parsed.get("failureReason") or ""),
        trajectory=trajectory,
        raw_output=stdout,
    )


def _build_prompt(task: dict[str, Any]) -> str:
    return f"""
You are an Autoppia miner trajectory finder.

Given one IWA task, produce a replayable trajectory as a list of tool calls.
Return only JSON matching the provided schema. Do not include markdown.

Task JSON:
{json.dumps(task, indent=2, ensure_ascii=True)}

Rules:
- The top-level output field must be `trajectory`.
- `trajectory` must be a list of tool calls: {{"name": "browser.navigate", "arguments": {{...}}}}.
- Prefer these tool names: browser.navigate, browser.click, browser.input, browser.select_dropdown, browser.send_keys, browser.wait, browser.done.
- Use stable selectors when possible. Prefer text, labels, semantic attributes, href, data-testid, or CSS selectors.
- Keep the trajectory short and replayable. Avoid coordinate clicks unless there is no stable selector.
- Do not invent final success. If you cannot infer a reliable trajectory, return success=false and the best partial trajectory.
- Never include secrets or API keys in the trajectory.

Expected output example:
{{
  "success": true,
  "confidence": 0.82,
  "summary": "Opened the page and clicked the requested control.",
  "trajectory": [
    {{"name": "browser.navigate", "arguments": {{"url": "https://example.com"}}}},
    {{"name": "browser.click", "arguments": {{"selector": {{"type": "textSelector", "value": "Continue"}}}}}}
  ]
}}
""".strip()


async def find_trayectory_with_claude_code(task: dict[str, Any]) -> TrajectoryResult:
    claude_bin = shutil.which(os.getenv("CLAUDE_CODE_BIN", "claude"))
    if not claude_bin:
        raise RuntimeError("Claude Code CLI is not installed or not on PATH")

    timeout = float(os.getenv("CLAUDE_CODE_TIMEOUT_SECONDS", "300"))
    model = os.getenv("CLAUDE_CODE_MODEL", "sonnet")
    max_budget_usd = os.getenv("CLAUDE_CODE_MAX_BUDGET_USD")

    cmd = [
        claude_bin,
        "--print",
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(TRAJECTORY_SCHEMA, ensure_ascii=True),
        "--model",
        model,
        "--dangerously-skip-permissions",
        "--permission-mode",
        "bypassPermissions",
        "--no-session-persistence",
    ]
    if max_budget_usd:
        cmd.extend(["--max-budget-usd", str(max_budget_usd)])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=os.environ.copy(),
    )
    try:
        stdout_raw, stderr_raw = await asyncio.wait_for(proc.communicate(_build_prompt(task).encode("utf-8")), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.communicate()
        raise TimeoutError(f"Claude Code timed out after {timeout:.0f}s") from exc

    stdout = stdout_raw.decode("utf-8", errors="replace")
    stderr = stderr_raw.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"Claude Code failed with exit code {proc.returncode}: {stderr[-1000:]}")

    return parse_claude_code_output(stdout)
