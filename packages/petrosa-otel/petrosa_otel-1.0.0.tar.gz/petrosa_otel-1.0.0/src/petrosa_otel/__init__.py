"""
Unified OpenTelemetry initialization for Petrosa services.

This package provides a standardized way to set up OpenTelemetry instrumentation
across all Petrosa services, eliminating code duplication and ensuring consistent
behavior.

Example usage:
    ```python
    from petrosa_otel import setup_telemetry, attach_logging_handler

    # Setup telemetry
    setup_telemetry(
        service_name="ta-bot",
        service_type="fastapi",
        enable_nats_propagation=True,
        enable_mysql=True,
        enable_mongodb=True
    )

    # Attach logging handler (for async services)
    attach_logging_handler()
    ```
"""

__version__ = "1.0.0"

from petrosa_otel.logging_handlers import attach_logging_handler
from petrosa_otel.setup import get_meter, get_tracer, setup_telemetry

__all__ = [
    "setup_telemetry",
    "get_tracer",
    "get_meter",
    "attach_logging_handler",
]

