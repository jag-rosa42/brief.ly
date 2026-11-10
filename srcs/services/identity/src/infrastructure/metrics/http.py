"""Prometheus metrics for the identity HTTP API."""

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator, metrics

SERVICE_NAME = "identity"
METRICS_HANDLER_PATTERN = r"^/metrics$"


def configure_http_metrics(app: FastAPI) -> None:
    """Count responses and observe duration with bounded, route-template labels."""
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_group_untemplated=True,
        excluded_handlers=[METRICS_HANDLER_PATTERN],
    )

    def set_service_label(info: metrics.Info) -> None:
        info.service = SERVICE_NAME  # ty: ignore[unresolved-attribute]

    instrumentator.add(
        set_service_label,
        metrics.requests(custom_labels={"service": SERVICE_NAME}),
        metrics.latency(
            should_include_status=False,
            custom_labels={"service": SERVICE_NAME},
        ),
    )
    instrumentator.instrument(app).expose(app, include_in_schema=False)
