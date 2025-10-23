"""
Base instrumentation utilities shared across frameworks.

This module provides common OpenTelemetry setup functionality that can be reused
across different framework instrumentations (LangChain, LlamaIndex, etc.).
"""

from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


def create_tracer_provider(
    resource_attributes: Optional[dict] = None,
) -> TracerProvider:
    """
    Create and configure an OpenTelemetry tracer provider.

    Args:
        resource_attributes: Resource attributes to include

    Returns:
        TracerProvider: Configured tracer provider
    """
    resource = Resource(attributes=resource_attributes or {})
    provider = TracerProvider(resource=resource)

    return provider


def create_otlp_exporter(
    endpoint: str,
    api_key: str,
    headers: Optional[dict] = None,
) -> OTLPSpanExporter:
    """
    Create an OTLP span exporter configured for TCC.

    Args:
        endpoint: OTLP endpoint URL
        api_key: TCC API key for authentication
        headers: Additional headers to include

    Returns:
        OTLPSpanExporter: Configured exporter
    """
    exporter_headers = {"Authorization": f"Bearer {api_key}"}
    if headers:
        exporter_headers.update(headers)

    return OTLPSpanExporter(
        endpoint=endpoint,
        headers=exporter_headers,
    )


def setup_instrumentation(
    api_key: str,
    endpoint: str,
    resource_attributes: Optional[dict] = None,
) -> TracerProvider:
    """
    Set up OpenTelemetry instrumentation with TCC configuration.

    This is a convenience function that creates a tracer provider, configures
    the OTLP exporter, and sets the global tracer provider.

    Args:
        api_key: TCC API key
        endpoint: OTLP endpoint URL
        resource_attributes: Resource attributes

    Returns:
        TracerProvider: The configured tracer provider
    """
    # Create tracer provider
    provider = create_tracer_provider(resource_attributes)

    # Create and configure exporter
    exporter = create_otlp_exporter(endpoint, api_key)

    # Add batch span processor
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    return provider
