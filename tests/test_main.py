from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "secureship"


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_security_headers():
    r = client.get("/")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in r.headers["Content-Security-Policy"]


def test_docs_disabled():
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_metrics_exposed():
    client.get("/health")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert 'http_requests_total{method="GET",path="/health",status="200"}' in r.text
