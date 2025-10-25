"""Tests for setup module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from petrosa_otel.setup import get_meter, get_tracer, setup_telemetry


class TestSetupTelemetry:
    """Tests for setup_telemetry function."""

    @patch.dict(os.environ, {"ENABLE_OTEL": "false"})
    def test_setup_disabled_when_otel_disabled(self):
        """Test that setup returns False when OTEL is disabled."""
        result = setup_telemetry(service_name="test-service")
        assert result is False

    @patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": ""})
    def test_setup_fails_without_endpoint(self):
        """Test that setup fails when no endpoint is configured."""
        result = setup_telemetry(service_name="test-service")
        assert result is False

    @patch.dict(
        os.environ,
        {
            "ENABLE_OTEL": "true",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
        },
    )
    @patch("petrosa_otel.setup.TracerProvider")
    @patch("petrosa_otel.setup.MeterProvider")
    @patch("petrosa_otel.setup.LoggerProvider")
    def test_setup_success_with_valid_config(
        self, mock_logger_provider, mock_meter_provider, mock_tracer_provider
    ):
        """Test successful setup with valid configuration."""
        result = setup_telemetry(
            service_name="test-service",
            service_version="1.0.0",
            service_type="async",
        )
        assert result is True

    @patch.dict(
        os.environ,
        {
            "ENABLE_OTEL": "true",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
        },
    )
    @patch("petrosa_otel.setup.TracerProvider")
    @patch("petrosa_otel.setup.MeterProvider")
    @patch("petrosa_otel.setup.LoggerProvider")
    @patch("petrosa_otel.setup.instrument_mongodb")
    def test_setup_uses_attribute_filter_with_mongodb(
        self,
        mock_instrument_mongodb,
        mock_logger_provider,
        mock_meter_provider,
        mock_tracer_provider,
    ):
        """Test that AttributeFilterSpanProcessor is used when MongoDB is enabled."""
        mock_tracer_instance = MagicMock()
        mock_tracer_provider.return_value = mock_tracer_instance

        result = setup_telemetry(
            service_name="test-service",
            enable_mongodb=True,
        )

        assert result is True
        # Verify add_span_processor was called
        assert mock_tracer_instance.add_span_processor.called

    @patch.dict(
        os.environ,
        {
            "ENABLE_OTEL": "true",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
            "ENABLE_TRACES": "false",
        },
    )
    @patch("petrosa_otel.setup.TracerProvider")
    def test_setup_respects_trace_disable(self, mock_tracer_provider):
        """Test that traces are not configured when disabled via env var."""
        result = setup_telemetry(
            service_name="test-service",
            enable_traces=True,  # Override with env var
        )
        # TracerProvider should not be created
        assert not mock_tracer_provider.called

    def test_get_tracer_returns_tracer(self):
        """Test that get_tracer returns a tracer instance."""
        tracer = get_tracer("test-tracer")
        assert tracer is not None

    def test_get_meter_returns_meter(self):
        """Test that get_meter returns a meter instance."""
        meter = get_meter("test-meter")
        assert meter is not None


class TestServiceTypes:
    """Tests for different service types."""

    @patch.dict(
        os.environ,
        {
            "ENABLE_OTEL": "true",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
        },
    )
    @patch("petrosa_otel.setup.LoggingInstrumentor")
    def test_fastapi_service_type_uses_correct_logging_format(
        self, mock_logging_instrumentor
    ):
        """Test that FastAPI service type preserves Uvicorn formatting."""
        mock_instrumentor_instance = MagicMock()
        mock_logging_instrumentor.return_value = mock_instrumentor_instance

        setup_telemetry(
            service_name="test-service",
            service_type="fastapi",
        )

        # Verify set_logging_format=False for FastAPI
        mock_instrumentor_instance.instrument.assert_called_once()
        call_kwargs = mock_instrumentor_instance.instrument.call_args[1]
        assert call_kwargs.get("set_logging_format") is False

    @patch.dict(
        os.environ,
        {
            "ENABLE_OTEL": "true",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
        },
    )
    @patch("petrosa_otel.setup.LoggingInstrumentor")
    @patch("petrosa_otel.logging_handlers.attach_logging_handler")
    def test_cronjob_auto_attaches_logging(
        self, mock_attach_handler, mock_logging_instrumentor
    ):
        """Test that CronJob service type auto-attaches logging handler."""
        setup_telemetry(
            service_name="test-service",
            service_type="cronjob",
            auto_attach_logging=True,
        )

        # Verify attach_logging_handler was called
        assert mock_attach_handler.called

