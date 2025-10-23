"""
OpenTelemetry instrumentation for LangChain applications.

This module provides automatic instrumentation of LangChain applications
to send traces to The Context Company platform.
"""

from typing import Optional

from opentelemetry.instrumentation.langchain import LangchainInstrumentor
from opentelemetry.sdk.trace import TracerProvider

from ._base import setup_instrumentation
from .config import (
    get_api_key,
    get_endpoint,
    configure_trace_content,
)


def instrument_langchain(
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    trace_content: bool = True,
) -> TracerProvider:
    """
    Initialize OpenTelemetry instrumentation for LangChain applications.

    This function configures the OpenTelemetry SDK with The Context Company
    platform and instruments LangChain to automatically capture traces.

    Custom metadata can be added to traces using LangChain's RunnableConfig:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke(
            "Hello!",
            {"metadata": {"serviceName": "my-app", "userId": "user_123"}}
        )

    Args:
        api_key: TCC API key. Defaults to TCC_API_KEY environment variable.
        endpoint: OTLP endpoint URL. Defaults to TCC_OTLP_URL environment variable
                 or https://api.thecontext.company/v1/traces
        trace_content: Whether to trace prompts and completions (default: True)

    Returns:
        TracerProvider: The configured tracer provider

    Raises:
        ValueError: If API key is not provided

    Example:
        >>> from tcc_otel import instrument_langchain
        >>> instrument_langchain(api_key="your-api-key")
        >>> # Now use LangChain as normal - all operations will be traced
    """
    # Get configuration values
    resolved_api_key = get_api_key(api_key)
    resolved_endpoint = get_endpoint(endpoint)

    # Configure trace content setting
    configure_trace_content(trace_content)

    # Set up OpenTelemetry instrumentation
    provider = setup_instrumentation(
        api_key=resolved_api_key,
        endpoint=resolved_endpoint,
    )

    # Instrument LangChain
    LangchainInstrumentor().instrument()

    print(f"✅ LangChain OpenTelemetry instrumentation initialized")
    print(f"   Exporting traces to: {resolved_endpoint}")
    print(f"   Trace content: {'enabled' if trace_content else 'disabled'}")

    return provider
