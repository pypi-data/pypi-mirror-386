"""
Redis-based message bus for distributed agent communication.

Implements explicit message passing between agents using Redis Streams.
Each agent consumes from its own queue and publishes results back.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

import redis
from pydantic import BaseModel, Field


class TaskMessage(BaseModel):
    """Message format for task distribution."""

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    source_agent: str
    target_agent: str
    payload_ref: str | None = Field(
        default=None, description="S3/MinIO reference for large payloads"
    )
    payload: dict[str, Any] | None = Field(
        default=None, description="Inline payload for small tasks"
    )
    trace_parent: str | None = Field(
        default=None, description="OpenTelemetry trace context"
    )
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ResponseMessage(BaseModel):
    """Response message from agent execution."""

    task_id: str
    job_id: str
    agent_name: str
    status: str  # "completed", "failed", "in_progress"
    artifact_ref: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    trace_parent: str | None = None
    completed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MessageBus:
    """Redis Streams-based message bus for agent communication."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize the message bus with Redis connection."""
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.agent_stream_prefix = "agent:stream:"
        self.response_stream = "responses:stream"

    def publish_task(self, message: TaskMessage) -> str:
        """
        Publish a task message to the target agent's stream.

        Args:
            message: TaskMessage to publish

        Returns:
            Message ID from Redis
        """
        stream_name = f"{self.agent_stream_prefix}{message.target_agent}"
        message_data = {"data": message.model_dump_json()}

        message_id = self.redis_client.xadd(stream_name, message_data)
        return message_id

    def consume_tasks(
        self, agent_name: str, block_ms: int = 5000, count: int = 1
    ) -> list[TaskMessage]:
        """
        Consume tasks from an agent's stream (blocking read).

        Args:
            agent_name: Name of the agent consuming tasks
            block_ms: Time to block waiting for messages (milliseconds)
            count: Number of messages to retrieve

        Returns:
            List of TaskMessage objects
        """
        stream_name = f"{self.agent_stream_prefix}{agent_name}"

        # Create consumer group if it doesn't exist
        try:
            self.redis_client.xgroup_create(
                stream_name, agent_name, id="0", mkstream=True
            )
        except redis.ResponseError:
            pass  # Group already exists

        # Read from stream
        messages = self.redis_client.xreadgroup(
            groupname=agent_name,
            consumername=agent_name,
            streams={stream_name: ">"},
            count=count,
            block=block_ms,
        )

        tasks = []
        if messages:
            for stream, stream_messages in messages:
                for msg_id, msg_data in stream_messages:
                    task_data = json.loads(msg_data["data"])
                    tasks.append(TaskMessage(**task_data))

                    # Acknowledge message
                    self.redis_client.xack(stream_name, agent_name, msg_id)

        return tasks

    def publish_response(self, response: ResponseMessage) -> str:
        """
        Publish a response message to the response stream.

        Args:
            response: ResponseMessage to publish

        Returns:
            Message ID from Redis
        """
        message_data = {"data": response.model_dump_json()}
        message_id = self.redis_client.xadd(self.response_stream, message_data)
        return message_id

    def register_agent(self, agent_name: str, metadata: dict[str, Any]) -> None:
        """
        Register an agent in the agent registry.

        Args:
            agent_name: Name of the agent
            metadata: Agent metadata (role, capabilities, status, etc.)
        """
        self.redis_client.hset(
            "agent:registry", agent_name, json.dumps(metadata)
        )

    def get_registered_agents(self) -> dict[str, dict[str, Any]]:
        """Get all registered agents and their metadata."""
        agents = self.redis_client.hgetall("agent:registry")
        return {name: json.loads(data) for name, data in agents.items()}

    def set_agent_status(self, agent_name: str, status: str) -> None:
        """Update agent status (active, idle, error)."""
        agent_data = self.redis_client.hget("agent:registry", agent_name)
        if agent_data:
            metadata = json.loads(agent_data)
            metadata["status"] = status
            metadata["last_heartbeat"] = datetime.utcnow().isoformat()
            self.redis_client.hset(
                "agent:registry", agent_name, json.dumps(metadata)
            )

    def get_queue_depth(self, agent_name: str) -> int:
        """Get the number of pending messages for an agent."""
        stream_name = f"{self.agent_stream_prefix}{agent_name}"
        try:
            info = self.redis_client.xinfo_stream(stream_name)
            return info.get("length", 0)
        except redis.ResponseError:
            return 0

    def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            return self.redis_client.ping()
        except Exception:
            return False
