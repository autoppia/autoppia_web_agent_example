from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agent
from claude_code_provider import TrajectoryResult, parse_claude_code_output


def test_parse_claude_code_output_accepts_structured_output_wrapper() -> None:
    stdout = json.dumps(
        {
            "type": "result",
            "structured_output": {
                "success": True,
                "confidence": 0.9,
                "summary": "ok",
                "trajectory": [
                    {
                        "name": "browser.navigate",
                        "arguments": {"url": "https://example.com"},
                    }
                ],
            },
        }
    )

    result = parse_claude_code_output(stdout)

    assert result.success is True
    assert result.confidence == 0.9
    assert result.trajectory == [
        {
            "name": "browser.navigate",
            "arguments": {"url": "https://example.com"},
        }
    ]


def test_parse_claude_code_output_normalizes_legacy_actions() -> None:
    stdout = json.dumps(
        {
            "success": True,
            "confidence": 1,
            "summary": "ok",
            "actions": [
                {
                    "action": "browser.click",
                    "args": {"selector": {"type": "textSelector", "value": "Continue"}},
                }
            ],
        }
    )

    result = parse_claude_code_output(stdout)

    assert result.trajectory == [
        {
            "name": "browser.click",
            "arguments": {"selector": {"type": "textSelector", "value": "Continue"}},
        }
    ]


def test_find_trayectory_endpoint_returns_trajectory(monkeypatch) -> None:
    async def fake_find_trayectory_with_claude_code(payload):
        assert payload["prompt"] == "Open homepage"
        return TrajectoryResult(
            success=True,
            confidence=0.8,
            summary="ok",
            trajectory=[
                {
                    "name": "browser.navigate",
                    "arguments": {"url": "https://example.com"},
                }
            ],
        )

    monkeypatch.setattr(agent, "find_trayectory_with_claude_code", fake_find_trayectory_with_claude_code)
    client = TestClient(agent.app)

    response = client.post(
        "/find_trayectory",
        json={"id": "t1", "prompt": "Open homepage", "url": "https://example.com"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["trajectory"] == [
        {
            "name": "browser.navigate",
            "arguments": {"url": "https://example.com"},
        }
    ]
