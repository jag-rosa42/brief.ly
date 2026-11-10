"""Prometheus metrics for the AI Processing HTTP API."""

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator, metrics

SERVICE_NAME = "ai-processing"
SERVICE_LABEL = "service"
METRICS_HANDLER_PATTERN = r"^/metrics$"


def configure_http_metrics(app: FastAPI) -> None:
    """Expose internal HTTP metrics with bounded labels and exact status codes.

    Count completed requests and record their duration for the fixed
    ``ai-processing`` service. Group unmatched paths (ex:/ai-processing/123)
    as ``none`` and exclude ``/metrics`` scrapes.
    """
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_group_untemplated=True,
        excluded_handlers=[METRICS_HANDLER_PATTERN],
    )

    def set_service_label(info: metrics.Info) -> None:
        info.service = SERVICE_NAME  # ty: ignore[unresolved-attribute]

    instrumentator.add(
        set_service_label,
        metrics.requests(custom_labels={SERVICE_LABEL: SERVICE_NAME}),
        metrics.latency(
            should_include_status=False,
            custom_labels={SERVICE_LABEL: SERVICE_NAME},
        ),
    )
    instrumentator.instrument(app).expose(app, include_in_schema=False)
