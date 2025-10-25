"""
Unified OpenTelemetry setup for all Petrosa services.
"""

import logging
import os
from typing import Literal

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from petrosa_otel.instrumentors import (
    instrument_fastapi,
    instrument_http,
    instrument_mongodb,
    instrument_mysql,
)
from petrosa_otel.logging_handlers import set_logger_provider
from petrosa_otel.processors import AttributeFilterSpanProcessor

logger = logging.getLogger(__name__)

ServiceType = Literal["fastapi", "async", "cronjob", "cli"]


def setup_telemetry(
    service_name: str,
    service_version: str | None = None,
    service_type: ServiceType = "async",
    otlp_endpoint: str | None = None,
    enable_metrics: bool = True,
    enable_traces: bool = True,
    enable_logs: bool = True,
    enable_http: bool = True,
    enable_mysql: bool = False,
    enable_mongodb: bool = False,
    enable_fastapi: bool = False,
    auto_attach_logging: bool = False,
) -> bool:
    """
    Set up OpenTelemetry instrumentation for a Petrosa service.

    This is the main entry point for configuring OpenTelemetry. It handles:
    - Resource creation with service metadata
    - Trace provider setup with OTLP exporter
    - Metrics provider setup with periodic export
    - Logging provider setup with OTLP exporter
    - Optional instrumentation for HTTP, MySQL, MongoDB, FastAPI

    Args:
        service_name: Name of the service (e.g., "ta-bot")
        service_version: Version of the service (defaults to OTEL_SERVICE_VERSION env var)
        service_type: Type of service - affects logging handler behavior:
            - "fastapi": FastAPI application (use Uvicorn's logging)
            - "async": Async service (NATS listener, WebSocket client)
            - "cronjob": Kubernetes CronJob
            - "cli": Command-line script
        otlp_endpoint: OTLP endpoint URL (defaults to OTEL_EXPORTER_OTLP_ENDPOINT env var)
        enable_metrics: Whether to enable metrics export
        enable_traces: Whether to enable trace export
        enable_logs: Whether to enable log export
        enable_http: Whether to instrument HTTP libraries (requests, urllib3)
        enable_mysql: Whether to instrument MySQL (PyMySQL)
        enable_mongodb: Whether to instrument MongoDB (PyMongo)
        enable_fastapi: Whether this is a FastAPI application
        auto_attach_logging: Whether to auto-attach logging handler (for async/cli/cronjob)

    Returns:
        True if setup successful, False otherwise

    Example:
        ```python
        from petrosa_otel import setup_telemetry

        # FastAPI service
        setup_telemetry(
            service_name="ta-bot",
            service_type="fastapi",
            enable_fastapi=True,
            enable_mysql=True,
            enable_mongodb=True
        )

        # Async NATS listener
        setup_telemetry(
            service_name="realtime-strategies",
            service_type="async",
            enable_mongodb=True,
            auto_attach_logging=True  # Attach logging immediately
        )

        # CronJob
        setup_telemetry(
            service_name="data-extractor",
            service_type="cronjob",
            enable_mysql=True,
            enable_mongodb=True,
            auto_attach_logging=True
        )
        ```
    """
    # Early return if OTEL disabled globally
    if os.getenv("ENABLE_OTEL", "true").lower() not in ("true", "1", "yes"):
        logger.info("OpenTelemetry is disabled (ENABLE_OTEL=false)")
        return False

    # Check if OpenTelemetry is already initialized by opentelemetry-instrument
    if os.getenv("OTEL_PYTHON_DISABLED_INSTRUMENTATIONS"):
        logger.info("🔍 OpenTelemetry already initialized by opentelemetry-instrument")
        # For pre-instrumented services, just attach logging if needed
        if auto_attach_logging and service_type in ("async", "cli", "cronjob"):
            from petrosa_otel.logging_handlers import attach_logging_handler

            attach_logging_handler()
        return True

    # Get configuration from environment variables
    service_version = service_version or os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
    otlp_endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if not otlp_endpoint:
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT not set - OpenTelemetry will not be initialized"
        )
        return False

    # Debug logging
    logger.info("🔍 OpenTelemetry setup:")
    logger.info(f"   Service: {service_name} v{service_version}")
    logger.info(f"   Type: {service_type}")
    logger.info(f"   Endpoint: {otlp_endpoint}")
    logger.info(f"   Traces: {enable_traces}, Metrics: {enable_metrics}, Logs: {enable_logs}")

    # Check environment variable overrides
    enable_metrics = enable_metrics and os.getenv("ENABLE_METRICS", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    enable_traces = enable_traces and os.getenv("ENABLE_TRACES", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    enable_logs = enable_logs and os.getenv("ENABLE_LOGS", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    # Create resource attributes
    resource_attributes = {
        "service.name": service_name,
        "service.version": service_version,
        "service.instance.id": os.getenv("HOSTNAME", "unknown"),
        "deployment.environment": os.getenv("ENVIRONMENT", "production"),
    }

    # Add custom resource attributes if provided
    custom_attributes = os.getenv("OTEL_RESOURCE_ATTRIBUTES")
    if custom_attributes:
        for attr in custom_attributes.split(","):
            if "=" in attr:
                key, value = attr.split("=", 1)
                resource_attributes[key.strip()] = value.strip()

    resource = Resource.create(resource_attributes)

    # Parse headers once for all exporters
    headers_env = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
    headers: dict[str, str] | None = None
    if headers_env:
        headers_list = [
            tuple(h.split("=", 1)) for h in headers_env.split(",") if "=" in h
        ]
        headers = dict(headers_list)

    # Set up tracing if enabled
    if enable_traces:
        try:
            tracer_provider = TracerProvider(resource=resource)
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                headers=headers,
            )

            # Use AttributeFilterSpanProcessor if MongoDB is enabled
            # This prevents errors from dict/list attributes in MongoDB spans
            if enable_mongodb:
                tracer_provider.add_span_processor(
                    AttributeFilterSpanProcessor(otlp_exporter)
                )
                logger.info("   Using AttributeFilterSpanProcessor for MongoDB compatibility")
            else:
                tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

            trace.set_tracer_provider(tracer_provider)
            logger.info(f"✅ OpenTelemetry tracing enabled for {service_name}")

        except Exception as e:
            logger.error(f"⚠️  Failed to set up OpenTelemetry tracing: {e}", exc_info=True)

    # Set up metrics if enabled
    if enable_metrics:
        try:
            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(
                    endpoint=otlp_endpoint,
                    headers=headers,
                ),
                export_interval_millis=int(
                    os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "60000")
                ),
            )

            meter_provider = MeterProvider(
                resource=resource, metric_readers=[metric_reader]
            )

            metrics.set_meter_provider(meter_provider)
            logger.info(f"✅ OpenTelemetry metrics enabled for {service_name}")

        except Exception as e:
            logger.error(f"⚠️  Failed to set up OpenTelemetry metrics: {e}")

    # Set up logging export via OTLP if enabled
    if enable_logs:
        try:
            # Enrich logs with trace context
            # For FastAPI, use set_logging_format=False to preserve Uvicorn formatting
            # For others, use set_logging_format=True for proper trace context injection
            set_logging_format = service_type != "fastapi"
            LoggingInstrumentor().instrument(
                set_logging_format=set_logging_format,
                log_level=logging.NOTSET,
            )

            log_exporter = OTLPLogExporter(
                endpoint=otlp_endpoint,
                headers=headers,
            )

            logger_provider = LoggerProvider(resource=resource)
            logger_provider.add_log_record_processor(
                BatchLogRecordProcessor(log_exporter)
            )

            # Store logger provider for later handler attachment
            set_logger_provider(logger_provider)

            logger.info(f"✅ OpenTelemetry logging export configured for {service_name}")

            # Auto-attach logging handler for non-FastAPI services
            if auto_attach_logging and service_type in ("async", "cli", "cronjob"):
                from petrosa_otel.logging_handlers import attach_logging_handler

                attach_logging_handler()
            elif service_type == "fastapi":
                logger.info(
                    "   Note: FastAPI uses Uvicorn's logging handlers automatically"
                )
            else:
                logger.info(
                    "   Note: Call attach_logging_handler() in main() to activate log export"
                )

        except Exception as e:
            logger.error(f"⚠️  Failed to set up OpenTelemetry logging export: {e}")

    # Instrument services
    if enable_http:
        instrument_http()

    if enable_mysql:
        instrument_mysql()

    if enable_mongodb:
        instrument_mongodb()

    if enable_fastapi:
        logger.info(
            "   Note: Call instrument_fastapi(app) after creating FastAPI app instance"
        )

    logger.info(f"🚀 OpenTelemetry setup completed for {service_name} v{service_version}")
    return True


def get_tracer(name: str | None = None) -> trace.Tracer:
    """
    Get a tracer instance.

    Args:
        name: Tracer name (defaults to package name)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name or "petrosa-otel")


def get_meter(name: str | None = None) -> metrics.Meter:
    """
    Get a meter instance.

    Args:
        name: Meter name (defaults to package name)

    Returns:
        Meter instance
    """
    return metrics.get_meter(name or "petrosa-otel")

