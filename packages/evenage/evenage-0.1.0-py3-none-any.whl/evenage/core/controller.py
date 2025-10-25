"""
Controller module for EvenAge.

Orchestrates job execution by distributing tasks to agents via message bus.
Replaces CrewAI's hidden "Crew" orchestration with explicit task distribution.
"""

from __future__ import annotations

import uuid
from typing import Any

from evenage.core.config import PipelineConfig
from evenage.core.message_bus import MessageBus, TaskMessage
from evenage.core.task import Task


class Controller:
    """
    Job controller that orchestrates task execution.

    The controller:
    1. Reads pipeline configuration
    2. Creates task messages
    3. Publishes to agent queues
    4. Monitors responses
    5. Manages dependencies
    """

    def __init__(self, message_bus: MessageBus):
        """
        Initialize controller with message bus.

        Args:
            message_bus: MessageBus instance for communication
        """
        self.message_bus = message_bus
        self.active_jobs: dict[str, dict[str, Any]] = {}

    def submit_job(self, pipeline: PipelineConfig, inputs: dict[str, Any] | None = None) -> str:
        """
        Submit a new job for execution.

        Args:
            pipeline: Pipeline configuration with tasks
            inputs: Input variables for the pipeline

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        inputs = inputs or {}

        # Create job tracking
        self.active_jobs[job_id] = {
            "pipeline": pipeline.name,
            "status": "running",
            "tasks": {},
            "results": {},
        }

        # Build task dependency graph
        task_map = {task.name: task for task in pipeline.tasks}

        # Submit tasks (respecting dependencies)
        for task_config in pipeline.tasks:
            self._submit_task(job_id, task_config, task_map, inputs)

        return job_id

    def _submit_task(
        self,
        job_id: str,
        task_config: Any,
        task_map: dict[str, Any],
        inputs: dict[str, Any],
    ) -> None:
        """
        Submit a task to the message bus.

        Args:
            job_id: Job identifier
            task_config: Task configuration
            task_map: Map of task names to configs
            inputs: Job inputs
        """
        # Gather context from dependencies
        context = ""
        for dep_name in task_config.context:
            if dep_name in self.active_jobs[job_id]["results"]:
                context += f"\n{dep_name}: {self.active_jobs[job_id]['results'][dep_name]}"

        # Interpolate inputs in description
        description = task_config.description
        for key, value in inputs.items():
            description = description.replace(f"{{{key}}}", str(value))

        # Create task message
        task_message = TaskMessage(
            job_id=job_id,
            source_agent="controller",
            target_agent=task_config.agent,
            payload={
                "name": task_config.name,
                "description": description,
                "context": context,
                "expected_output": task_config.expected_output,
            },
        )

        # Publish to agent queue
        self.message_bus.publish_task(task_message)

        # Track task
        self.active_jobs[job_id]["tasks"][task_config.name] = {
            "task_id": task_message.task_id,
            "status": "submitted",
            "agent": task_config.agent,
        }

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """
        Get the status of a job.

        Args:
            job_id: Job identifier

        Returns:
            Job status dictionary or None if not found
        """
        return self.active_jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled, False if not found
        """
        if job_id in self.active_jobs:
            self.active_jobs[job_id]["status"] = "cancelled"
            return True
        return False

    def list_active_jobs(self) -> list[dict[str, Any]]:
        """List all active jobs."""
        return [
            {"job_id": job_id, **details}
            for job_id, details in self.active_jobs.items()
            if details["status"] == "running"
        ]
