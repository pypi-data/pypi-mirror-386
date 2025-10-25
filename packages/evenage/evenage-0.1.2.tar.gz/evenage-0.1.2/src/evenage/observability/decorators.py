"""
Decorators for transparent observability.

Users can easily add/remove observability by adding/removing decorators.
All observability is opt-in and explicit.
"""

from __future__ import annotations

import functools
import time
from typing import Any, Callable

from .metrics import get_metrics_service
from .storage_integration import get_response_storage
from .tracing import get_tracing_service


def observe(
    operation_name: str | None = None,
    enable_tracing: bool = True,
    enable_metrics: bool = True,
    store_result: bool = False,
):
    """
    Main observability decorator - wraps functions with tracing and metrics.

    Usage:
        @observe("my_operation")
        def my_function():
            return "result"

        # Or disable specific features:
        @observe("my_operation", enable_tracing=False)
        def my_function():
            return "result"

    Args:
        operation_name: Name for the operation (defaults to function name)
        enable_tracing: Enable OpenTelemetry tracing
        enable_metrics: Enable Prometheus metrics
        store_result: Store result in storage service

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            op_name = operation_name or func.__name__
            start_time = time.time()

            # Get services
            tracing = get_tracing_service() if enable_tracing else None
            metrics = get_metrics_service() if enable_metrics else None
            storage = get_response_storage() if store_result else None

            # Extract context from arguments (if available)
            agent_name = kwargs.get("agent_name") or getattr(args[0], "name", "unknown")

            # Start trace
            trace_context = None
            if tracing and tracing.enabled:
                trace_context = tracing.tracer.start_as_current_span(
                    op_name,
                    attributes={
                        "agent.name": agent_name,
                        "operation": op_name,
                    },
                )
                trace_context.__enter__()

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Record metrics
                if metrics and metrics.enabled:
                    duration = time.time() - start_time
                    metrics.task_duration.labels(
                        agent_name=agent_name, status="success"
                    ).observe(duration)

                # Store result if needed
                if storage and result:
                    storage.store_if_large(result, agent_name, op_name)

                # Add success status to trace
                if trace_context:
                    trace_context.__exit__(None, None, None)

                return result

            except Exception as e:
                # Record error
                if metrics and metrics.enabled:
                    metrics.record_error(agent_name, type(e).__name__)

                # Add error to trace
                if trace_context:
                    trace_context.__exit__(type(e), e, e.__traceback__)

                raise

        return wrapper

    return decorator


def trace_llm_call(
    enable_tracing: bool = True,
    enable_metrics: bool = True,
):
    """
    Decorator specifically for LLM calls.

    Captures LLM-specific metrics like tokens, latency, model name.

    Usage:
        @trace_llm_call()
        def call_llm(self, prompt: str) -> str:
            # LLM call
            return response

    Args:
        enable_tracing: Enable OpenTelemetry tracing
        enable_metrics: Enable Prometheus metrics
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            # Get services
            tracing = get_tracing_service() if enable_tracing else None
            metrics = get_metrics_service() if enable_metrics else None

            # Extract LLM context
            self_obj = args[0] if args else None
            agent_name = getattr(self_obj, "name", "unknown")
            model = getattr(self_obj, "llm_model", "unknown")

            # Start trace
            trace_context = None
            if tracing and tracing.enabled:
                trace_context = tracing.tracer.start_as_current_span(
                    "llm.call",
                    attributes={
                        "agent.name": agent_name,
                        "llm.model": model,
                        "llm.provider": getattr(self_obj, "llm_provider", "unknown"),
                    },
                )
                trace_context.__enter__()

            try:
                # Execute LLM call
                result = func(*args, **kwargs)

                # Extract token usage if available
                tokens = 0
                if hasattr(result, "tokens_used"):
                    tokens = result.tokens_used
                elif isinstance(result, dict) and "tokens" in result:
                    tokens = result["tokens"]

                # Record metrics
                if metrics and metrics.enabled:
                    duration = time.time() - start_time
                    metrics.task_duration.labels(
                        agent_name=agent_name, status="success"
                    ).observe(duration)

                    if tokens > 0:
                        metrics.tokens_total.labels(
                            agent_name=agent_name, model=model
                        ).inc(tokens)

                # Add attributes to trace
                if trace_context:
                    span = trace_context.tracer.get_current_span()
                    if span:
                        span.set_attribute("llm.tokens", tokens)
                        span.set_attribute("llm.latency_ms", int(duration * 1000))
                    trace_context.__exit__(None, None, None)

                return result

            except Exception as e:
                if metrics and metrics.enabled:
                    metrics.record_error(agent_name, f"llm_{type(e).__name__}")

                if trace_context:
                    trace_context.__exit__(type(e), e, e.__traceback__)

                raise

        return wrapper

    return decorator


def store_large_response(
    size_threshold_kb: int = 100,
    store_in_minio: bool = True,
):
    """
    Decorator to automatically store large responses in MinIO.

    Usage:
        @store_large_response(size_threshold_kb=50)
        def process_large_data(self, data):
            # Process data
            return large_result

    Args:
        size_threshold_kb: Size threshold in KB to trigger storage
        store_in_minio: Enable MinIO storage

    Returns:
        Decorated function that returns either the result or a storage reference
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)

            if not store_in_minio or not result:
                return result

            storage = get_response_storage()

            # Check size and store if needed
            stored_result = storage.store_if_large(
                result,
                agent_name=getattr(args[0], "name", "unknown"),
                operation=func.__name__,
                size_threshold_kb=size_threshold_kb,
            )

            return stored_result

        return wrapper

    return decorator


def disable_observability(func: Callable) -> Callable:
    """
    Decorator to explicitly disable ALL observability for a function.

    Usage:
        @disable_observability
        def sensitive_operation(self):
            # No tracing, metrics, or storage
            return result
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Simply execute without any observability
        return func(*args, **kwargs)

    return wrapper
