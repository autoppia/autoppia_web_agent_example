from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agent


def test_find_trayectory_endpoint_returns_template_trajectory() -> None:
    client = TestClient(agent.app)

    response = client.post(
        "/find_trayectory",
        json={"id": "t1", "prompt": "Open homepage", "url": "https://example.com"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["trajectory"] == []
    assert body["web_agent_id"] == "autoppia-web-agent-example"
