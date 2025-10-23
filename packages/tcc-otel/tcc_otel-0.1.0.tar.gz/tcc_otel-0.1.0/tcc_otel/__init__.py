"""
TCC OpenTelemetry SDK for Python.

This package provides OpenTelemetry instrumentation for Python frameworks
to send traces to The Context Company platform.

Usage:
    >>> from tcc_otel import instrument_langchain
    >>> instrument_langchain(api_key="...")
"""

from .langchain import instrument_langchain

__version__ = "0.1.0"
__all__ = ["instrument_langchain"]
