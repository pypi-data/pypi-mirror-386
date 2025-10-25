"""
Configuration schemas and validation for EvenAge projects.

Uses Pydantic for type-safe YAML configuration parsing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator

from .errors import InvalidConfigError


class LLMConfig(BaseModel):
    """LLM configuration schema."""

    provider: str = Field(..., description="LLM provider (openai, anthropic, gemini, groq)")
    model: str = Field(..., description="Model name")
    api_key: str = Field(..., description="API key or env var reference")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, gt=0, description="Max output tokens")
    timeout: Optional[int] = Field(default=None, gt=0, description="Request timeout in seconds")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        if not v or v.strip() == "":
            raise ValueError("API key cannot be empty")
        return v


class AgentConfigSchema(BaseModel):
    """Agent configuration schema (agent.yml)."""

    name: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role description")
    goal: str = Field(..., description="Agent goal")
    backstory: Optional[str] = Field(default=None, description="Agent backstory")
    llm: Union[str, LLMConfig] = Field(..., description="LLM configuration")
    tools: List[str] = Field(default_factory=list, description="List of tool names")
    max_iterations: int = Field(default=15, gt=0, description="Maximum task iterations")
    allow_delegation: bool = Field(default=False, description="Allow agent delegation")
    verbose: bool = Field(default=True, description="Verbose logging")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate agent name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Agent name must be alphanumeric (with underscores/hyphens)")
        return v

    @classmethod
    def load_from_file(cls, path: Path) -> "AgentConfigSchema":
        """Load agent config from YAML file.

        Args:
            path: Path to agent.yml

        Returns:
            Parsed agent configuration

        Raises:
            InvalidConfigError: If config is invalid
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return cls(**data)
        except FileNotFoundError:
            raise InvalidConfigError(str(path), "File not found")
        except yaml.YAMLError as e:
            raise InvalidConfigError(str(path), f"Invalid YAML: {e}")
        except Exception as e:
            raise InvalidConfigError(str(path), str(e))


class TaskConfigSchema(BaseModel):
    """Task configuration schema (used in pipelines)."""

    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Task description")
    agent: str = Field(..., description="Agent to execute task")
    expected_output: str = Field(..., description="Expected output description")
    tools: List[str] = Field(default_factory=list, description="Tools available for task")
    context: List[str] = Field(default_factory=list, description="Context from other tasks")
    async_execution: bool = Field(default=False, description="Execute task asynchronously")


class PipelineConfigSchema(BaseModel):
    """Pipeline configuration schema (pipeline.yml)."""

    name: str = Field(..., description="Pipeline name")
    description: Optional[str] = Field(default=None, description="Pipeline description")
    tasks: List[TaskConfigSchema] = Field(..., description="List of tasks")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate pipeline name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Pipeline name must be alphanumeric (with underscores/hyphens)")
        return v

    @classmethod
    def load_from_file(cls, path: Path) -> "PipelineConfigSchema":
        """Load pipeline config from YAML file.

        Args:
            path: Path to pipeline.yml

        Returns:
            Parsed pipeline configuration

        Raises:
            InvalidConfigError: If config is invalid
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return cls(**data)
        except FileNotFoundError:
            raise InvalidConfigError(str(path), "File not found")
        except yaml.YAMLError as e:
            raise InvalidConfigError(str(path), f"Invalid YAML: {e}")
        except Exception as e:
            raise InvalidConfigError(str(path), str(e))


class ProjectConfigSchema(BaseModel):
    """Project configuration schema (evenage.yml)."""

    project: ProjectDetails = Field(..., description="Project details")

    @classmethod
    def load_from_file(cls, path: Path) -> "ProjectConfigSchema":
        """Load project config from YAML file.

        Args:
            path: Path to evenage.yml

        Returns:
            Parsed project configuration

        Raises:
            InvalidConfigError: If config is invalid
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return cls(**data)
        except FileNotFoundError:
            raise InvalidConfigError(str(path), "File not found")
        except yaml.YAMLError as e:
            raise InvalidConfigError(str(path), f"Invalid YAML: {e}")
        except Exception as e:
            raise InvalidConfigError(str(path), str(e))

    def save_to_file(self, path: Path) -> None:
        """Save project config to YAML file.

        Args:
            path: Path to evenage.yml

        Raises:
            InvalidConfigError: If save fails
        """
        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.model_dump(exclude_none=True),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                )
        except Exception as e:
            raise InvalidConfigError(str(path), f"Failed to save: {e}")


class ProjectDetails(BaseModel):
    """Project details section."""

    name: str = Field(..., description="Project name")
    broker: str = Field(default="redis", description="Message broker type")
    database: str = Field(default="postgres", description="Database type")
    storage: str = Field(default="minio", description="Storage backend")
    tracing: bool = Field(default=True, description="Enable tracing")
    metrics: bool = Field(default=True, description="Enable metrics")
    agents: List[str] = Field(default_factory=list, description="List of agent names")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Project name must be alphanumeric (with underscores/hyphens)")
        return v


def validate_project_directory(path: Path) -> bool:
    """Check if a directory contains a valid EvenAge project.

    Args:
        path: Directory path to check

    Returns:
        True if valid project directory
    """
    return (path / "evenage.yml").exists()


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Find the root directory of an EvenAge project.

    Args:
        start_path: Starting directory (default: current directory)

    Returns:
        Project root path, or None if not found
    """
    current = start_path or Path.cwd()

    # Check current directory and all parents
    for directory in [current, *current.parents]:
        if validate_project_directory(directory):
            return directory

    return None
