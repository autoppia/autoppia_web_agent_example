from fastapi.testclient import TestClient
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api import app


client = TestClient(app)


def _sample_observation() -> dict:
    return {
        "html_dom": "<html></html>",
        "screenshot": {"media_type": "image/png", "data": "dGVzdA=="},
        "task_prompt": "Do a simple thing",
        "previous_actions": [],
        "url": "https://example.com",
    }


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_act_returns_empty_actions():
    response = client.post("/act", json=_sample_observation())
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 1


def test_solve_task_mock_response():
    response = client.post("/solve_task", json=_sample_observation())
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "completed"
    assert isinstance(payload["actions"], list)
    assert len(payload["actions"]) >= 1
    assert payload["final_answer"] is not None
    assert "summary" in payload


def test_solve_task_accepts_validator_shape():
    validator_payload = {
        "prompt": "Do a thing",
        "url": "https://example.com",
        "html": "<html></html>",
        "screenshot": "dGVzdA==",
    }
    response = client.post("/solve_task", json=validator_payload)
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert isinstance(payload["actions"], list) and payload["actions"]
