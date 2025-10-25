"""Tests for logging_handlers module."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from petrosa_otel.logging_handlers import (
    attach_logging_handler,
    get_logger_provider,
    set_logger_provider,
)


class TestLoggingHandlers:
    """Tests for logging handlers."""

    def test_set_and_get_logger_provider(self):
        """Test setting and getting logger provider."""
        mock_provider = MagicMock()
        set_logger_provider(mock_provider)
        assert get_logger_provider() == mock_provider

    def test_attach_logging_handler_without_provider(self):
        """Test that attach fails when no provider is set."""
        # Clear provider
        set_logger_provider(None)

        result = attach_logging_handler()
        assert result is False

    @patch("petrosa_otel.logging_handlers.LoggingHandler")
    def test_attach_logging_handler_success(self, mock_logging_handler):
        """Test successful logging handler attachment."""
        # Set up mock provider
        mock_provider = MagicMock()
        set_logger_provider(mock_provider)

        # Mock handler
        mock_handler_instance = MagicMock()
        mock_logging_handler.return_value = mock_handler_instance

        result = attach_logging_handler()
        assert result is True

        # Verify handler was added to root logger
        root_logger = logging.getLogger()
        assert mock_handler_instance in root_logger.handlers

        # Cleanup
        root_logger.removeHandler(mock_handler_instance)

    @patch("petrosa_otel.logging_handlers.LoggingHandler")
    def test_attach_logging_handler_idempotent(self, mock_logging_handler):
        """Test that attaching handler multiple times is idempotent."""
        # Set up mock provider
        mock_provider = MagicMock()
        set_logger_provider(mock_provider)

        # Mock handler
        mock_handler_instance = MagicMock()
        mock_logging_handler.return_value = mock_handler_instance

        # First attachment
        result1 = attach_logging_handler()
        assert result1 is True

        # Second attachment (should recognize existing handler)
        result2 = attach_logging_handler()
        assert result2 is True

        # Cleanup
        root_logger = logging.getLogger()
        if mock_handler_instance in root_logger.handlers:
            root_logger.removeHandler(mock_handler_instance)

