"""
Worker module for EvenAge.

Each worker consumes tasks from Redis for a specific agent and executes them.
Designed to run as a separate container per agent.
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from pathlib import Path

from evenage.core.agent import Agent
from evenage.core.config import AgentConfig, EvenAgeConfig, load_agent_config
from evenage.core.message_bus import MessageBus
from evenage.database.models import DatabaseService
from evenage.observability.metrics import get_metrics_service, init_metrics
from evenage.observability.tracing import get_tracing_service, init_tracing
from evenage.observability.storage_integration import init_response_storage
from evenage.storage.minio_storage import StorageService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Worker:
    """
    Worker that processes tasks for a specific agent.

    Each worker:
    1. Consumes tasks from Redis stream
    2. Executes via agent
    3. Publishes results back
    4. Emits traces and metrics
    """

    def __init__(
        self,
        agent_name: str,
        config: EvenAgeConfig,
        agent_config: AgentConfig,
    ):
        """
        Initialize worker.

        Args:
            agent_name: Name of the agent this worker handles
            config: EvenAge configuration
            agent_config: Agent-specific configuration
        """
        self.agent_name = agent_name
        self.config = config
        self.running = False

        # Initialize services
        self.message_bus = MessageBus(config.redis_url)
        self.storage = StorageService(
            endpoint=config.minio_endpoint,
            access_key=config.minio_access_key,
            secret_key=config.minio_secret_key,
            secure=config.minio_secure,
            bucket=config.minio_bucket,
        )
        self.database = DatabaseService(config.database_url)

        # Initialize observability
        if config.enable_tracing:
            init_tracing(
                service_name=f"evenage-worker-{agent_name}",
                otlp_endpoint=config.otel_exporter_otlp_endpoint,
            )

        if config.enable_metrics:
            init_metrics(port=config.prometheus_metrics_port)

        # Initialize response storage (for large LLM outputs)
        init_response_storage(
            storage_service=self.storage,
            enabled=config.enable_large_response_storage,
            default_threshold_kb=config.storage_threshold_kb,
        )

        # Create agent (map AgentConfig.llm to Agent fields)
        llm_provider = "ollama"
        llm_model = "llama2"
        llm_api_key = None
        llm_api_base = None
        temperature = 0.7
        max_tokens = 2048

        try:
            if isinstance(agent_config.llm, dict):
                llm_provider = agent_config.llm.get("provider", llm_provider)
                llm_model = agent_config.llm.get("model", llm_model)
                llm_api_key = agent_config.llm.get("api_key", None)
                llm_api_base = agent_config.llm.get("api_base", None)
                temperature = agent_config.llm.get("temperature", temperature)
                max_tokens = agent_config.llm.get("max_tokens", max_tokens)
            elif isinstance(agent_config.llm, str):
                # Treat string as model name using OpenAI by default
                llm_provider = "openai"
                llm_model = agent_config.llm
        except Exception:
            # Keep defaults if anything goes wrong parsing llm config
            pass

        self.agent = Agent(
            name=agent_config.name,
            role=agent_config.role,
            goal=agent_config.goal,
            backstory=agent_config.backstory,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
            llm_api_base=llm_api_base,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=agent_config.tools,
            max_iterations=agent_config.max_iterations,
            allow_delegation=agent_config.allow_delegation,
            verbose=agent_config.verbose,
        )

        # Initialize agent with message bus and empty tool registry
        self.agent.initialize(self.message_bus, {})

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"Worker initialized for agent: {agent_name}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def start(self) -> None:
        """Start the worker loop."""
        self.running = True
        logger.info(f"Worker started for agent: {self.agent_name}")

        # Update agent status
        self.message_bus.set_agent_status(self.agent_name, "idle")

        while self.running:
            try:
                # Consume tasks from Redis (blocking read)
                tasks = self.message_bus.consume_tasks(
                    self.agent_name,
                    block_ms=5000,  # 5 second timeout
                    count=1,
                )

                if not tasks:
                    continue

                for task_message in tasks:
                    self._process_task(task_message)

            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                get_metrics_service().record_error(self.agent_name, type(e).__name__)
                time.sleep(1)  # Brief pause before retrying

        # Cleanup
        self.message_bus.set_agent_status(self.agent_name, "offline")
        logger.info("Worker stopped")

    def _process_task(self, task_message) -> None:
        """
        Process a single task.

        Args:
            task_message: TaskMessage from message bus
        """
        start_time = time.time()
        tracing = get_tracing_service()
        metrics = get_metrics_service()

        logger.info(
            f"Processing task {task_message.task_id} for job {task_message.job_id}"
        )

        # Start trace
        with tracing.trace_task_execution(
            task_id=task_message.task_id,
            agent_name=self.agent_name,
            task_description=task_message.payload.get("description", "")
            if task_message.payload
            else "",
        ) as span:
            try:
                # Execute task
                response = self.agent.execute_task(task_message)

                # Publish response
                self.message_bus.publish_response(response)

                # Record metrics
                duration = time.time() - start_time
                metrics.record_task_execution(
                    agent_name=self.agent_name,
                    duration_seconds=duration,
                    status=response.status,
                    tokens=response.metrics.get("tokens", 0),
                )

                # Save trace to database
                self.database.save_trace(
                    task_id=task_message.task_id,
                    job_id=task_message.job_id,
                    agent_name=self.agent_name,
                    status=response.status,
                    duration_ms=int(duration * 1000),
                    tokens_used=response.metrics.get("tokens", 0),
                )

                logger.info(
                    f"Task {task_message.task_id} completed with status: {response.status}"
                )

                if span:
                    span.set_attribute("task.status", response.status)
                    span.set_attribute("task.tokens", response.metrics.get("tokens", 0))

            except Exception as e:
                logger.error(f"Error processing task: {e}", exc_info=True)

                # Record error
                metrics.record_error(self.agent_name, type(e).__name__)

                # Send error response
                from evenage.core.message_bus import ResponseMessage

                error_response = ResponseMessage(
                    task_id=task_message.task_id,
                    job_id=task_message.job_id,
                    agent_name=self.agent_name,
                    status="failed",
                    error=str(e),
                )
                self.message_bus.publish_response(error_response)


def main():
    """Main entry point for worker."""
    # Load configuration
    config = EvenAgeConfig()

    # Get agent name from environment
    agent_name = config.agent_name or os.getenv("AGENT_NAME")
    if not agent_name:
        logger.error("AGENT_NAME environment variable not set")
        sys.exit(1)

    # Load agent configuration
    agent_config_path = Path(f"agents/{agent_name}/agent.yml")
    if not agent_config_path.exists():
        logger.error(f"Agent configuration not found: {agent_config_path}")
        sys.exit(1)

    agent_config = load_agent_config(agent_config_path)

    # Create and start worker
    worker = Worker(agent_name, config, agent_config)
    worker.start()


if __name__ == "__main__":
    main()
