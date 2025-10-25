"""
Observability package for EvenAge.

Provides decorators and utilities for transparent tracing, metrics, and storage.
Users can easily enable/disable observability features via decorators or config.
"""

from .decorators import observe, store_large_response, trace_llm_call
from .metrics import MetricsService, get_metrics_service, init_metrics
from .storage_integration import ResponseStorage, get_response_storage
from .tracing import TracingService, get_tracing_service, init_tracing

__all__ = [
    # Services
    "TracingService",
    "MetricsService",
    "ResponseStorage",
    # Initialization
    "init_tracing",
    "init_metrics",
    # Getters
    "get_tracing_service",
    "get_metrics_service",
    "get_response_storage",
    # Decorators (main user-facing API)
    "observe",
    "trace_llm_call",
    "store_large_response",
]
