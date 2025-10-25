"""Tests for processors module."""

from unittest.mock import MagicMock

import pytest

from petrosa_otel.processors import AttributeFilterSpanProcessor


class TestAttributeFilterSpanProcessor:
    """Tests for AttributeFilterSpanProcessor."""

    def test_filters_dict_attributes_on_start(self):
        """Test that dict attributes are filtered on span start."""
        # Create mock span with dict attribute
        span = MagicMock()
        span._attributes = {
            "valid_string": "value",
            "valid_int": 123,
            "invalid_dict": {"nested": "value"},
        }

        # Create processor
        exporter = MagicMock()
        processor = AttributeFilterSpanProcessor(exporter)

        # Call on_start
        processor.on_start(span)

        # Verify dict was removed
        assert "valid_string" in span._attributes
        assert "valid_int" in span._attributes
        assert "invalid_dict" not in span._attributes

    def test_filters_list_attributes_on_end(self):
        """Test that list attributes are filtered on span end."""
        # Create mock span with list attribute
        span = MagicMock()
        span._attributes = {
            "valid_string": "value",
            "invalid_list": [1, 2, 3],
        }

        # Create processor
        exporter = MagicMock()
        processor = AttributeFilterSpanProcessor(exporter)

        # Call on_end
        processor.on_end(span)

        # Verify list was removed
        assert "valid_string" in span._attributes
        assert "invalid_list" not in span._attributes

    def test_handles_span_without_attributes(self):
        """Test that processor handles spans without attributes."""
        # Create mock span without _attributes
        span = MagicMock()
        del span._attributes

        # Create processor
        exporter = MagicMock()
        processor = AttributeFilterSpanProcessor(exporter)

        # Should not raise error
        processor.on_start(span)
        processor.on_end(span)

    def test_preserves_valid_attribute_types(self):
        """Test that valid attribute types are preserved."""
        # Create mock span with various valid types
        span = MagicMock()
        span._attributes = {
            "string": "value",
            "int": 123,
            "float": 45.67,
            "bool": True,
            "none": None,
        }

        # Create processor
        exporter = MagicMock()
        processor = AttributeFilterSpanProcessor(exporter)

        # Call on_start
        processor.on_start(span)

        # Verify all valid types are preserved
        assert len(span._attributes) == 5
        assert span._attributes["string"] == "value"
        assert span._attributes["int"] == 123
        assert span._attributes["float"] == 45.67
        assert span._attributes["bool"] is True
        assert span._attributes["none"] is None

