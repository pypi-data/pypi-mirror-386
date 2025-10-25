"""
Canonical Agent base for EvenAge (Tier 0).

Defines AgentBase with explicit message-bus interactions and LLM hooks.
"""
from __future__ import annotations

import time
from typing import Any, Optional

from pydantic import BaseModel, Field

from evenage.core.message_bus_base import (
    MessageBusBase as MessageBus,
    ResponseMessage,
    TaskMessage,
)
from evenage.llm import create_llm_provider, LLMConfig
from evenage.observability import observe, store_large_response, trace_llm_call


class AgentBase(BaseModel):
    """
    EvenAge Agent with explicit communication model.

    Consume tasks from Redis streams, execute with visible LLM interactions,
    publish results back to the message bus, and emit telemetry.
    """

    name: str = Field(description="Agent identifier (must be unique)")
    role: str = Field(description="Agent role/persona")
    goal: str = Field(description="Agent's primary objective")
    backstory: str | None = Field(
        default=None, description="Agent backstory for context"
    )

    # LLM Configuration (local-first default)
    llm_provider: str = Field(
        default="ollama", description="LLM provider (ollama, llamacpp, openai, anthropic, gemini, groq)"
    )
    llm_model: str = Field(default="llama2", description="Model name for the provider")
    llm_api_key: Optional[str] = Field(default=None, description="API key for cloud providers")
    llm_api_base: Optional[str] = Field(default=None, description="API base URL for custom endpoints")
    temperature: float = Field(default=0.7, description="LLM temperature")
    max_tokens: int = Field(default=2048, description="Max tokens to generate")

    # Tools and capabilities
    tools: list[str] = Field(default_factory=list, description="List of tool names available to agent")

    # Execution settings
    max_iterations: int = Field(default=15, description="Maximum reasoning iterations")
    allow_delegation: bool = Field(default=False, description="Allow delegating tasks to other agents")
    verbose: bool = Field(default=True, description="Enable verbose logging")

    # Internal state (not part of config)
    _message_bus: MessageBus | None = None
    _tool_registry: dict[str, Any] | None = None
    _llm_provider: Any = None

    class Config:
        arbitrary_types_allowed = True

    def initialize(self, message_bus: MessageBus, tool_registry: dict[str, Any]) -> None:
        """Initialize agent with message bus and tool registry."""
        self._message_bus = message_bus
        self._tool_registry = tool_registry

        # Initialize LLM provider
        llm_config = LLMConfig(
            provider=self.llm_provider,
            model=self.llm_model,
            api_key=self.llm_api_key,
            api_base=self.llm_api_base,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        self._llm_provider = create_llm_provider(llm_config)

        # Register agent in Redis
        metadata = {
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "tools": self.tools,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "status": "idle",
        }
        message_bus.register_agent(self.name, metadata)

    @observe(operation_name="task_execution", enable_tracing=True, enable_metrics=True)
    @store_large_response(size_threshold_kb=100, store_in_minio=True)
    def execute_task(self, task_message: TaskMessage) -> ResponseMessage:
        """Execute a task received from the message bus and return a response."""
        start_time = time.time()

        try:
            # Update status
            if self._message_bus:
                self._message_bus.set_agent_status(self.name, "active")

            # Extract task payload
            payload = task_message.payload or {}
            task_description = payload.get("description", "")
            context = payload.get("context", "")

            # Build prompt
            prompt = self._build_prompt(task_description, context)

            # Execute LLM call
            result = self._execute_llm(prompt)

            # Build response
            response = ResponseMessage(
                task_id=task_message.task_id,
                job_id=task_message.job_id,
                agent_name=self.name,
                status="completed",
                result={"output": result},
                metrics={
                    "tokens": len(result.split()),  # Simplified token count
                    "latency_ms": int((time.time() - start_time) * 1000),
                },
                trace_parent=task_message.trace_parent,
            )

            # Update status
            if self._message_bus:
                self._message_bus.set_agent_status(self.name, "idle")

            return response

        except Exception as e:
            # Error handling
            return ResponseMessage(
                task_id=task_message.task_id,
                job_id=task_message.job_id,
                agent_name=self.name,
                status="failed",
                error=str(e),
                metrics={
                    "latency_ms": int((time.time() - start_time) * 1000),
                },
                trace_parent=task_message.trace_parent,
            )

    def _build_prompt(self, task: str, context: str) -> str:
        """Build prompt from agent config and task details."""
        prompt = f"""You are {self.role}.

Your goal: {self.goal}

{self.backstory if self.backstory else ''}

Available tools: {', '.join(self.tools) if self.tools else 'None'}

Context from previous tasks:
{context}

Current task:
{task}

Please complete this task:"""
        return prompt

    @trace_llm_call(enable_tracing=True, enable_metrics=True)
    def _execute_llm(self, prompt: str) -> str:
        """Execute LLM call using configured provider."""
        if not self._llm_provider:
            raise RuntimeError(f"Agent {self.name} not initialized. Call initialize() first.")

        # Build system prompt
        system_prompt = f"You are {self.role}. {self.goal}"
        if self.backstory:
            system_prompt += f"\n\n{self.backstory}"

        response = self._llm_provider.complete(
            prompt=prompt,
            system_prompt=system_prompt,
        )

        if self.verbose:
            import logging
            logging.getLogger("evenage.agent").info(
                "[%s] LLM response (%s/%s): %s tokens, %s",
                self.name,
                getattr(response, "provider", "unknown"),
                getattr(response, "model", "unknown"),
                getattr(response, "tokens_used", 0),
                getattr(response, "finish_reason", "unknown"),
            )

        return response.content

    def to_dict(self) -> dict[str, Any]:
        """Export agent configuration as dictionary."""
        return self.model_dump(exclude={"_message_bus", "_tool_registry"})


__all__ = ["AgentBase"]
