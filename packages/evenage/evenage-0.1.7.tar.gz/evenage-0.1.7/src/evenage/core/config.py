"""
Configuration management for EvenAge.

Handles loading and validating evenage.yml and pipeline.yml configurations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class EvenAgeConfig(BaseSettings):
    """Environment-based configuration for EvenAge runtime."""

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/evenage",
        description="PostgreSQL connection URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )

    # MinIO/S3 Storage
    minio_endpoint: str = Field(default="localhost:9000", description="MinIO endpoint")
    minio_access_key: str = Field(default="minioadmin", description="MinIO access key")
    minio_secret_key: str = Field(
        default="minioadmin123", description="MinIO secret key"
    )
    minio_secure: bool = Field(default=False, description="Use HTTPS for MinIO")
    minio_bucket: str = Field(default="evenage", description="Default bucket name")

    # OpenTelemetry
    otel_exporter_otlp_endpoint: str = Field(
        default="http://localhost:4318", description="OTLP endpoint for traces"
    )
    otel_service_name: str = Field(
        default="evenage", description="Service name for tracing"
    )
    enable_tracing: bool = Field(default=True, description="Enable OpenTelemetry tracing")

    # Prometheus
    prometheus_metrics_port: int = Field(
        default=8001, description="Port for Prometheus metrics"
    )
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")

    # Large Response Storage
    enable_large_response_storage: bool = Field(
        default=True, description="Enable automatic storage of large responses in MinIO"
    )
    storage_threshold_kb: int = Field(
        default=100, description="Size threshold in KB for storing responses in MinIO"
    )

    # API
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")

    # Agent worker settings
    agent_name: str | None = Field(
        default=None, description="Agent name for worker mode"
    )
    worker_concurrency: int = Field(
        default=1, description="Number of concurrent tasks per worker"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ProjectConfig(BaseModel):
    """Project configuration from evenage.yml."""

    name: str = Field(description="Project name")
    broker: str = Field(default="redis", description="Message broker type")
    database: str = Field(default="postgres", description="Database type")
    storage: str = Field(default="minio", description="Storage backend")
    tracing: bool = Field(default=True, description="Enable tracing")
    metrics: bool = Field(default=True, description="Enable metrics")
    large_response_storage: bool = Field(
        default=True, description="Enable automatic large response storage"
    )
    storage_threshold_kb: int = Field(
        default=100, description="Storage threshold in KB"
    )
    agents: list[str] = Field(default_factory=list, description="List of agent names")


class AgentConfig(BaseModel):
    """Agent configuration."""

    name: str
    role: str
    goal: str
    backstory: str | None = None
    llm: str | dict[str, Any] = Field(default="gpt-4")
    tools: list[str] = Field(default_factory=list)
    max_iterations: int = Field(default=15)
    allow_delegation: bool = Field(default=False)
    verbose: bool = Field(default=True)
    
    # Observability overrides (agent-specific)
    observability: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent-specific observability settings"
    )


class PipelineTask(BaseModel):
    """Task definition in a pipeline."""

    name: str
    description: str
    agent: str
    expected_output: str | None = None
    context: list[str] = Field(
        default_factory=list, description="Task IDs this task depends on"
    )
    tools: list[str] = Field(default_factory=list)
    async_execution: bool = Field(default=False)


class PipelineConfig(BaseModel):
    """Pipeline configuration from pipeline.yml."""

    name: str
    description: str | None = None
    tasks: list[PipelineTask]


def load_project_config(path: Path | str = "evenage.yml") -> ProjectConfig:
    """Load project configuration from YAML file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    return ProjectConfig(**data.get("project", {}))


def load_agent_config(path: Path | str) -> AgentConfig:
    """Load agent configuration from YAML file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Agent configuration not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    return AgentConfig(**data)


def load_pipeline_config(path: Path | str) -> PipelineConfig:
    """Load pipeline configuration from YAML file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Pipeline configuration not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    return PipelineConfig(**data)


def save_project_config(config: ProjectConfig, path: Path | str = "evenage.yml") -> None:
    """Save project configuration to YAML file."""
    path = Path(path)
    data = {"project": config.model_dump(exclude_none=True)}

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
