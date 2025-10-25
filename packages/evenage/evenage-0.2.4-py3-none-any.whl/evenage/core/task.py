"""
Task module for EvenAge.

Explicit task definitions without hidden orchestration.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Task(BaseModel):
    """
    Task definition for EvenAge.

    Unlike CrewAI's opaque task execution, EvenAge tasks are explicit:
    - Clear input/output contracts
    - Visible dependencies
    - Traceable execution
    """

    name: str = Field(description="Task identifier")
    description: str = Field(description="Task description/prompt")
    agent: str = Field(description="Agent name to execute this task")
    expected_output: str | None = Field(
        default=None, description="Expected output format/schema"
    )
    context: list[str] = Field(
        default_factory=list, description="Task IDs this task depends on"
    )
    tools: list[str] = Field(
        default_factory=list, description="Additional tools for this task"
    )
    async_execution: bool = Field(
        default=False, description="Execute asynchronously"
    )

    # Execution results (populated after execution)
    output: str | None = None
    status: str = "pending"  # pending, running, completed, failed
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Export task as dictionary."""
        return self.model_dump()
