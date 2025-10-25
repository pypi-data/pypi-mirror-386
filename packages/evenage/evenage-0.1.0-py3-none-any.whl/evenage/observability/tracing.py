"""
OpenTelemetry tracing integration for EvenAge.

Provides transparent observability for all agent operations.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


class TracingService:
    """OpenTelemetry tracing service for EvenAge."""

    def __init__(
        self,
        service_name: str = "evenage",
        otlp_endpoint: str = "http://localhost:4318/v1/traces",
        enabled: bool = True,
    ):
        """
        Initialize tracing service.

        Args:
            service_name: Service name for traces
            otlp_endpoint: OTLP endpoint URL
            enabled: Enable or disable tracing
        """
        self.enabled = enabled
        self.service_name = service_name

        if not enabled:
            logger.info("Tracing is disabled")
            return

        # Create resource with service name
        resource = Resource(attributes={"service.name": service_name})

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Add OTLP exporter
        try:
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            logger.info(f"Tracing initialized: {otlp_endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}")
            self.enabled = False

        self.tracer = trace.get_tracer(__name__)

    @contextmanager
    def trace_task_execution(
        self,
        task_id: str,
        agent_name: str,
        task_description: str,
        attributes: dict[str, Any] | None = None,
    ):
        """
        Context manager for tracing task execution.

        Usage:
            with tracer.trace_task_execution(task_id, agent, desc) as span:
                result = execute_task()
                span.set_attribute("result_length", len(result))

        Args:
            task_id: Task identifier
            agent_name: Agent executing the task
            task_description: Task description
            attributes: Additional span attributes
        """
        if not self.enabled:
            yield None
            return

        span_attributes = {
            "task.id": task_id,
            "agent.name": agent_name,
            "task.description": task_description[:200],  # Truncate
        }

        if attributes:
            span_attributes.update(attributes)

        with self.tracer.start_as_current_span(
            f"task.{agent_name}", attributes=span_attributes
        ) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    @contextmanager
    def trace_llm_call(
        self,
        model: str,
        prompt_length: int,
        attributes: dict[str, Any] | None = None,
    ):
        """
        Context manager for tracing LLM API calls.

        Args:
            model: LLM model name
            prompt_length: Length of prompt in tokens
            attributes: Additional attributes
        """
        if not self.enabled:
            yield None
            return

        span_attributes = {
            "llm.model": model,
            "llm.prompt_length": prompt_length,
        }

        if attributes:
            span_attributes.update(attributes)

        with self.tracer.start_as_current_span(
            "llm.call", attributes=span_attributes
        ) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    @contextmanager
    def trace_tool_execution(
        self,
        tool_name: str,
        attributes: dict[str, Any] | None = None,
    ):
        """
        Context manager for tracing tool executions.

        Args:
            tool_name: Name of the tool
            attributes: Additional attributes
        """
        if not self.enabled:
            yield None
            return

        span_attributes = {"tool.name": tool_name}

        if attributes:
            span_attributes.update(attributes)

        with self.tracer.start_as_current_span(
            f"tool.{tool_name}", attributes=span_attributes
        ) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add an event to the current span."""
        if not self.enabled:
            return

        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes=attributes or {})


# Global tracing service instance
_tracing_service: TracingService | None = None


def init_tracing(
    service_name: str = "evenage",
    otlp_endpoint: str = "http://localhost:4318/v1/traces",
    enabled: bool = True,
) -> TracingService:
    """
    Initialize global tracing service.

    Args:
        service_name: Service name for traces
        otlp_endpoint: OTLP endpoint URL
        enabled: Enable or disable tracing

    Returns:
        TracingService instance
    """
    global _tracing_service
    _tracing_service = TracingService(service_name, otlp_endpoint, enabled)
    return _tracing_service


def get_tracing_service() -> TracingService:
    """Get the global tracing service instance."""
    if _tracing_service is None:
        return init_tracing()
    return _tracing_service
