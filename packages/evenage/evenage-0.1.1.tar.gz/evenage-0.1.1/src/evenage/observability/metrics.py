"""
Prometheus metrics integration for EvenAge.

Exposes metrics for monitoring agent performance and system health.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from prometheus_client import Counter, Gauge, Histogram, start_http_server

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MetricsService:
    """Prometheus metrics service for EvenAge."""

    def __init__(self, port: int = 8001, enabled: bool = True):
        """
        Initialize metrics service.

        Args:
            port: Port to expose metrics on
            enabled: Enable or disable metrics
        """
        self.enabled = enabled
        self.port = port

        if not enabled:
            logger.info("Metrics are disabled")
            return

        # Task metrics
        self.task_duration = Histogram(
            "evenage_agent_task_duration_seconds",
            "Time spent executing tasks",
            ["agent_name", "status"],
        )

        self.task_total = Counter(
            "evenage_agent_tasks_total",
            "Total number of tasks processed",
            ["agent_name", "status"],
        )

        # Queue metrics
        self.queue_depth = Gauge(
            "evenage_queue_depth",
            "Number of pending messages in agent queue",
            ["agent_name"],
        )

        # Token metrics
        self.tokens_total = Counter(
            "evenage_tokens_total",
            "Total tokens consumed",
            ["agent_name", "model"],
        )

        # Error metrics
        self.errors_total = Counter(
            "evenage_errors_total",
            "Total errors encountered",
            ["agent_name", "error_type"],
        )

        # System metrics
        self.agents_active = Gauge(
            "evenage_agents_active",
            "Number of active agents",
        )

        self.jobs_running = Gauge(
            "evenage_jobs_running",
            "Number of running jobs",
        )

        # Start metrics server
        try:
            start_http_server(port)
            logger.info(f"Metrics server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            self.enabled = False

    def record_task_execution(
        self,
        agent_name: str,
        duration_seconds: float,
        status: str,
        tokens: int = 0,
        model: str = "unknown",
    ) -> None:
        """
        Record task execution metrics.

        Args:
            agent_name: Agent that executed the task
            duration_seconds: Execution time in seconds
            status: Task status (completed, failed, etc.)
            tokens: Number of tokens consumed
            model: LLM model used
        """
        if not self.enabled:
            return

        self.task_duration.labels(agent_name=agent_name, status=status).observe(
            duration_seconds
        )
        self.task_total.labels(agent_name=agent_name, status=status).inc()

        if tokens > 0:
            self.tokens_total.labels(agent_name=agent_name, model=model).inc(tokens)

    def record_error(self, agent_name: str, error_type: str) -> None:
        """
        Record an error.

        Args:
            agent_name: Agent where error occurred
            error_type: Type of error
        """
        if not self.enabled:
            return

        self.errors_total.labels(agent_name=agent_name, error_type=error_type).inc()

    def update_queue_depth(self, agent_name: str, depth: int) -> None:
        """
        Update queue depth for an agent.

        Args:
            agent_name: Agent name
            depth: Current queue depth
        """
        if not self.enabled:
            return

        self.queue_depth.labels(agent_name=agent_name).set(depth)

    def update_active_agents(self, count: int) -> None:
        """Update the count of active agents."""
        if not self.enabled:
            return

        self.agents_active.set(count)

    def update_running_jobs(self, count: int) -> None:
        """Update the count of running jobs."""
        if not self.enabled:
            return

        self.jobs_running.set(count)


# Global metrics service instance
_metrics_service: MetricsService | None = None


def init_metrics(port: int = 8001, enabled: bool = True) -> MetricsService:
    """
    Initialize global metrics service.

    Args:
        port: Port to expose metrics on
        enabled: Enable or disable metrics

    Returns:
        MetricsService instance
    """
    global _metrics_service
    _metrics_service = MetricsService(port, enabled)
    return _metrics_service


def get_metrics_service() -> MetricsService:
    """Get the global metrics service instance."""
    if _metrics_service is None:
        return init_metrics()
    return _metrics_service
