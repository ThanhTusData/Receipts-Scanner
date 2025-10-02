# tests/test_metrics.py
from fastapi.testclient import TestClient
from api.main import app

def test_metrics_endpoint():
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    ct = r.headers.get("content-type", "")
    assert "text/plain" in ct or "application/openmetrics-text" in ct
    # metrics should include api_request_total even if zero
    assert "api_request_total" in r.text
