"""
Service-specific OpenTelemetry instrumentation.
"""

import logging

logger = logging.getLogger(__name__)


def instrument_http():
    """
    Instrument HTTP libraries (requests, urllib3).

    This is used by all services that make HTTP calls.
    """
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor

        RequestsInstrumentor().instrument()
        URLLib3Instrumentor().instrument()
        logger.info("✅ HTTP instrumentation enabled")
        return True
    except Exception as e:
        logger.warning(f"⚠️  Failed to instrument HTTP libraries: {e}")
        return False


def instrument_fastapi(app):
    """
    Instrument a FastAPI application.

    Args:
        app: FastAPI application instance

    Returns:
        True if successful, False otherwise
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logger.info("✅ FastAPI instrumentation enabled")
        return True
    except ImportError:
        logger.warning(
            "⚠️  opentelemetry-instrumentation-fastapi not installed. "
            "Install with: pip install petrosa-otel[fastapi]"
        )
        return False
    except Exception as e:
        logger.warning(f"⚠️  Failed to instrument FastAPI: {e}")
        return False


def instrument_mysql():
    """
    Instrument PyMySQL for MySQL database tracing.

    Returns:
        True if successful, False otherwise
    """
    try:
        from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor

        PyMySQLInstrumentor().instrument()
        logger.info("✅ MySQL instrumentation enabled")
        return True
    except ImportError:
        logger.warning(
            "⚠️  opentelemetry-instrumentation-pymysql not installed. "
            "Install with: pip install petrosa-otel[mysql]"
        )
        return False
    except Exception as e:
        logger.warning(f"⚠️  Failed to instrument MySQL: {e}")
        return False


def instrument_mongodb():
    """
    Instrument PyMongo for MongoDB database tracing.

    Note: Requires AttributeFilterSpanProcessor to avoid errors with
    dict/list attributes in spans.

    Returns:
        True if successful, False otherwise
    """
    try:
        from opentelemetry.instrumentation.pymongo import PymongoInstrumentor

        PymongoInstrumentor().instrument()
        logger.info("✅ MongoDB instrumentation enabled")
        return True
    except ImportError:
        logger.warning(
            "⚠️  opentelemetry-instrumentation-pymongo not installed. "
            "Install with: pip install petrosa-otel[mongodb]"
        )
        return False
    except Exception as e:
        logger.warning(f"⚠️  Failed to instrument MongoDB: {e}")
        return False

