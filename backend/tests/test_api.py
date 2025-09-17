from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_analyze_persian_positive():
    payload = {"text": "این یک روز عالی و بسیار خوب است 😊"}
    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert isinstance(data, dict)
    assert "label" in data
    assert "scores" in data
    assert set(data["scores"].keys()) == {"positive", "negative", "neutral"}

    # Expect a generally positive label for this input
    assert data["label"] in {"positive", "neutral"}
    assert data["scores"]["positive"] >= data["scores"]["negative"]


