"""HTTP metric contract for the content-management app."""

from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.main import app


def _sample(metrics_text: str, name: str, labels: dict[str, str]) -> float:
    prefix = name + "{"
    for line in metrics_text.splitlines():
        if not line.startswith(prefix):
            continue
        series, value = line.split(" ", 1)
        if all(f'{key}="{label}"' in series for key, label in labels.items()):
            return float(value)
    return 0.0


def test_http_metrics_use_bounded_labels_and_count_503() -> None:
    @app.get("/metric-check/{item_id}")
    def metric_check(item_id: str) -> dict[str, str]:
        if item_id == "failure":
            raise HTTPException(status_code=503, detail="sensitive failure detail")
        return {"item_id": item_id}

    with TestClient(app) as client:
        before = client.get("/metrics").text
        assert client.get("/metric-check/private-123").status_code == 200
        assert client.get("/metric-check/failure").status_code == 503
        assert client.get("/unmatched/private-456").status_code == 404
        after = client.get("/metrics").text

    success = {
        "service": "content-management",
        "handler": "/metric-check/{item_id}",
        "method": "GET",
        "status": "200",
    }
    failure = {**success, "status": "503"}
    unmatched = {**success, "handler": "none", "status": "404"}
    for labels in (success, failure, unmatched):
        assert _sample(after, "http_requests_total", labels) == (
            _sample(before, "http_requests_total", labels) + 1
        )

    duration_labels = {key: value for key, value in success.items() if key != "status"}
    assert _sample(after, "http_request_duration_seconds_count", duration_labels) == (
        _sample(before, "http_request_duration_seconds_count", duration_labels) + 2
    )
    assert "private-123" not in after
    assert "private-456" not in after
    assert "sensitive failure detail" not in after
    assert 'handler="/metrics"' not in after
