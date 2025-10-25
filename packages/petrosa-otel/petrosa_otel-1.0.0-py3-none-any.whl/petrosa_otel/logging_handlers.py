"""
OpenTelemetry logging handlers for different service types.
"""

import logging

logger = logging.getLogger(__name__)

# Global references to logger provider and handler
_global_logger_provider = None
_otlp_logging_handler = None


def set_logger_provider(logger_provider):
    """
    Set the global logger provider for later handler attachment.

    This is called by setup_telemetry() and should not be called directly.

    Args:
        logger_provider: OpenTelemetry LoggerProvider instance
    """
    global _global_logger_provider
    _global_logger_provider = logger_provider


def attach_logging_handler():
    """
    Attach OTLP logging handler to root logger.

    For async services without Uvicorn (WebSocket clients, NATS listeners,
    CLI jobs, CronJobs). This attaches the OTLP handler to the root logger
    to enable log export to the OTLP endpoint.

    Call this in main() after setup_telemetry() to activate log export.

    Returns:
        True if successful, False otherwise

    Example:
        ```python
        from petrosa_otel import setup_telemetry, attach_logging_handler

        # Setup telemetry first
        setup_telemetry(service_name="my-service")

        # Then attach logging handler
        attach_logging_handler()

        # Now logs will be exported to OTLP
        logger = logging.getLogger(__name__)
        logger.info("This log will be exported!")
        ```
    """
    global _global_logger_provider, _otlp_logging_handler

    if _global_logger_provider is None:
        logger.warning(
            "⚠️  Logger provider not configured - logging export not available. "
            "Make sure to call setup_telemetry() first."
        )
        return False

    try:
        from opentelemetry.sdk._logs import LoggingHandler

        root_logger = logging.getLogger()

        # Check if handler already attached
        if _otlp_logging_handler is not None:
            if _otlp_logging_handler in root_logger.handlers:
                logger.info("✅ OTLP logging handler already attached")
                return True

        # Create and attach handler
        handler = LoggingHandler(
            level=logging.NOTSET,
            logger_provider=_global_logger_provider,
        )

        root_logger.addHandler(handler)
        _otlp_logging_handler = handler

        logger.info("✅ OTLP logging handler attached to root logger")
        logger.info(f"   Total handlers: {len(root_logger.handlers)}")

        return True

    except Exception as e:
        logger.error(f"⚠️  Failed to attach logging handler: {e}")
        return False


def get_logger_provider():
    """
    Get the global logger provider.

    Returns:
        LoggerProvider instance or None if not configured
    """
    return _global_logger_provider

