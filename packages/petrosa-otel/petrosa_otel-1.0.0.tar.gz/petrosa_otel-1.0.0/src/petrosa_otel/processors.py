"""
Custom OpenTelemetry span processors.
"""

from opentelemetry.sdk.trace.export import BatchSpanProcessor


class AttributeFilterSpanProcessor(BatchSpanProcessor):
    """
    Custom span processor that filters out invalid attribute values before export.

    OpenTelemetry only allows primitive types (str, int, float, bool, bytes) or None
    as attribute values. This processor filters out dict and list values that can
    be produced by MongoDB instrumentation.

    This prevents errors like:
        TypeError: Invalid type list for attribute value

    Usage:
        ```python
        from opentelemetry.sdk.trace import TracerProvider
        from petrosa_otel.processors import AttributeFilterSpanProcessor

        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(
            AttributeFilterSpanProcessor(otlp_exporter)
        )
        ```
    """

    def on_start(self, span, parent_context=None):
        """Clean attributes when span starts."""
        super().on_start(span, parent_context)
        self._clean_attributes(span)

    def on_end(self, span):
        """Clean attributes when span ends."""
        self._clean_attributes(span)
        super().on_end(span)

    def _clean_attributes(self, span):
        """
        Remove invalid attribute values from span.

        Removes dict and list values which are not supported by OpenTelemetry.
        """
        if not hasattr(span, "_attributes") or not span._attributes:
            return

        # Identify invalid attributes
        invalid_keys = []
        for key, value in span._attributes.items():
            if isinstance(value, dict | list):
                invalid_keys.append(key)

        # Remove invalid attributes
        for key in invalid_keys:
            del span._attributes[key]

