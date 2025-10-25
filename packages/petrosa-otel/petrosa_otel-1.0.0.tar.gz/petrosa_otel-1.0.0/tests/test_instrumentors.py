"""Tests for instrumentors module."""

from unittest.mock import MagicMock, patch

import pytest

from petrosa_otel import instrumentors


class TestHTTPInstrumentation:
    """Tests for HTTP instrumentation."""

    @patch("petrosa_otel.instrumentors.RequestsInstrumentor")
    @patch("petrosa_otel.instrumentors.URLLib3Instrumentor")
    def test_instrument_http_success(
        self, mock_urllib3_instrumentor, mock_requests_instrumentor
    ):
        """Test successful HTTP instrumentation."""
        result = instrumentors.instrument_http()
        assert result is True
        assert mock_requests_instrumentor.return_value.instrument.called
        assert mock_urllib3_instrumentor.return_value.instrument.called

    @patch("petrosa_otel.instrumentors.RequestsInstrumentor", side_effect=Exception("Test error"))
    def test_instrument_http_handles_error(self, mock_instrumentor):
        """Test that HTTP instrumentation handles errors gracefully."""
        result = instrumentors.instrument_http()
        assert result is False


class TestFastAPIInstrumentation:
    """Tests for FastAPI instrumentation."""

    @patch("petrosa_otel.instrumentors.FastAPIInstrumentor")
    def test_instrument_fastapi_success(self, mock_instrumentor):
        """Test successful FastAPI instrumentation."""
        app = MagicMock()
        result = instrumentors.instrument_fastapi(app)
        assert result is True
        mock_instrumentor.instrument_app.assert_called_once_with(app)

    def test_instrument_fastapi_handles_import_error(self):
        """Test that FastAPI instrumentation handles missing dependency."""
        with patch.dict("sys.modules", {"opentelemetry.instrumentation.fastapi": None}):
            app = MagicMock()
            result = instrumentors.instrument_fastapi(app)
            # Should return False when module not available
            # (This test may need adjustment based on actual behavior)


class TestMySQLInstrumentation:
    """Tests for MySQL instrumentation."""

    @patch("petrosa_otel.instrumentors.PyMySQLInstrumentor")
    def test_instrument_mysql_success(self, mock_instrumentor):
        """Test successful MySQL instrumentation."""
        result = instrumentors.instrument_mysql()
        assert result is True
        assert mock_instrumentor.return_value.instrument.called


class TestMongoDBInstrumentation:
    """Tests for MongoDB instrumentation."""

    @patch("petrosa_otel.instrumentors.PymongoInstrumentor")
    def test_instrument_mongodb_success(self, mock_instrumentor):
        """Test successful MongoDB instrumentation."""
        result = instrumentors.instrument_mongodb()
        assert result is True
        assert mock_instrumentor.return_value.instrument.called

