"""
Configuration management for TCC OpenTelemetry instrumentation.

Handles environment variables, defaults, and validation for the SDK.
"""

import os
from typing import Optional


# Default values
DEFAULT_ENDPOINT = "https://api.thecontext.company/v1/traces"


def get_api_key(api_key: Optional[str] = None) -> str:
    """
    Get TCC API key from parameter or environment variable.

    Args:
        api_key: Optional API key parameter

    Returns:
        str: The API key

    Raises:
        ValueError: If API key is not provided
    """
    key = api_key or os.getenv("TCC_API_KEY")
    if not key:
        raise ValueError(
            "TCC API key is required. Set TCC_API_KEY environment variable "
            "or pass api_key parameter to the instrument function."
        )
    return key


def get_endpoint(endpoint: Optional[str] = None) -> str:
    """
    Get OTLP endpoint URL from parameter or environment variable.

    Args:
        endpoint: Optional endpoint parameter

    Returns:
        str: The endpoint URL
    """
    return endpoint or os.getenv("TCC_OTLP_URL", DEFAULT_ENDPOINT)


def configure_trace_content(trace_content: bool) -> None:
    """
    Configure whether to trace prompts and completions.

    This sets the TRACELOOP_TRACE_CONTENT environment variable which is
    used by OpenTelemetry instrumentation libraries.

    Args:
        trace_content: Whether to capture prompt/completion content
    """
    if not trace_content:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
    elif "TRACELOOP_TRACE_CONTENT" not in os.environ:
        # Ensure it's set to true if not already configured
        os.environ["TRACELOOP_TRACE_CONTENT"] = "true"
