"""
Init command for EvenAge CLI.

Creates new EvenAge projects with full scaffolding.
"""

from __future__ import annotations

from pathlib import Path

import click
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils import (
    NestedProjectError,
    ProjectConfigSchema,
    ProjectDetails,
    ProjectExistsError,
    get_template_renderer,
    print_panel,
    print_success,
    validate_project_directory,
    write_file,
)


@click.command()
@click.argument("project_name", required=False)
@click.option("--path", default=".", help="Path to create project in")
def init(project_name: str | None, path: str):
    """Initialize a new EvenAge project.
    
    Creates project structure with:
    - Core modules (Tier 1)
    - Configuration files
    - Docker setup
    - Default researcher agent
    - Example pipeline
    
    Examples:
        evenage init myproject
        evenage init myproject --path /path/to/dir
        evenage init  # Interactive mode
    """
    # Prompt for project name if not provided
    if not project_name:
        project_name = click.prompt("Project name")

    # Resolve project path
    project_path = Path(path)
    if project_name and project_name != ".":
        project_path = project_path / project_name
    project_path = project_path.resolve()

    # Check if project already exists
    if project_path.exists() and validate_project_directory(project_path):
        raise ProjectExistsError(str(project_path))

    # Check for nested project
    for parent in project_path.parents:
        if validate_project_directory(parent):
            raise NestedProjectError(str(parent))

    # Handle in-place creation
    create_in_place = False
    if project_name in (".", ""):
        create_in_place = True
    else:
        cwd_name = Path.cwd().name
        if path in (".", "") and project_name == cwd_name:
            create_in_place = True

    if create_in_place:
        project_path = Path.cwd().resolve()

    # Check if directory is empty (except for existing evenage.yml)
    if project_path.exists() and any(project_path.iterdir()):
        if not validate_project_directory(project_path):
            raise ProjectExistsError(str(project_path))

    print_panel(
        "Initializing EvenAge Project",
        f"Creating project: [bold]{project_path.name}[/bold]",
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("Creating project structure...", total=None)

        # Create directory structure
        _create_directories(project_path)

        # Generate core modules
        progress.update(task, description="Generating core modules...")
        _generate_core_modules(project_path)

        # Generate configuration files
        progress.update(task, description="Creating configuration...")
        _generate_config_files(project_path, project_path.name)

        # Generate Docker setup
        progress.update(task, description="Creating Docker configuration...")
        _generate_docker_setup(project_path)

        # Generate default agent
        progress.update(task, description="Seeding default agent...")
        _generate_default_agent(project_path)

        # Generate README
        progress.update(task, description="Creating README...")
        _generate_readme(project_path, project_path.name)

    print_success(f"Project created: {project_path}")
    print_panel(
        "Next Steps",
        f"cd {project_path if project_path != Path.cwd() else '.'}\nevenage run dev",
        style="green",
    )


def _create_directories(project_path: Path) -> None:
    """Create project directory structure."""
    directories = [
        project_path,
        project_path / "core",
        project_path / "agents",
        project_path / "workers",
        project_path / "pipelines",
        project_path / "docker",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def _generate_core_modules(project_path: Path) -> None:
    """Generate Tier 1 core modules."""
    renderer = get_template_renderer()
    core_path = project_path / "core"

    # Core __init__.py
    write_file(
        core_path / "__init__.py",
        "# Tier 1: Project Core - Imports and re-exports EvenAge base classes\n",
    )

    # Core modules from templates
    renderer.render_to_file("core_message_bus.py.j2", core_path / "message_bus.py", {})
    renderer.render_to_file("core_database.py.j2", core_path / "database.py", {})
    renderer.render_to_file("core_agent_runtime.py.j2", core_path / "agent_runtime.py", {})
    renderer.render_to_file("core_controller.py.j2", core_path / "controller.py", {})
    renderer.render_to_file("core_config.py.j2", core_path / "config.py", {})


def _generate_config_files(project_path: Path, project_name: str) -> None:
    """Generate configuration files."""
    renderer = get_template_renderer()

    # evenage.yml
    config = ProjectConfigSchema(
        project=ProjectDetails(
            name=project_name,
            broker="redis",
            database="postgres",
            storage="minio",
            tracing=True,
            metrics=True,
            agents=[],
        )
    )
    config.save_to_file(project_path / "evenage.yml")

    # .env
    renderer.render_to_file("dotenv.j2", project_path / ".env", {})

    # docker/prometheus.yml
    renderer.render_to_file(
        "prometheus.yml.j2",
        project_path / "docker" / "prometheus.yml",
        {},
    )


def _generate_docker_setup(project_path: Path) -> None:
    """Generate Docker configuration."""
    renderer = get_template_renderer()

    renderer.render_to_file("docker-compose.yml.j2", project_path / "docker-compose.yml", {})
    renderer.render_to_file("Dockerfile.j2", project_path / "Dockerfile", {})
    renderer.render_to_file("requirements.txt.j2", project_path / "requirements.txt", {})


def _generate_default_agent(project_path: Path) -> None:
    """Generate default researcher agent."""
    agent_name = "researcher"
    renderer = get_template_renderer()

    # Agent directory structure
    agent_path = project_path / "agents" / agent_name
    tools_path = agent_path / "tools"
    agent_path.mkdir(parents=True, exist_ok=True)
    tools_path.mkdir(parents=True, exist_ok=True)

    # __init__ files
    write_file(project_path / "agents" / "__init__.py", "")
    write_file(agent_path / "__init__.py", "")
    write_file(tools_path / "__init__.py", "")

    # Agent configuration
    agent_context = {
        "agent_name": agent_name,
        "role": "Research Agent",
        "goal": "Research topics on the web and summarize findings concisely.",
        "backstory": "A helpful researcher that gathers and condenses information from reliable web sources.",
        "llm_provider": "gemini",
        "llm_model": "gemini-2.0-flash-exp",
        "llm_api_key_var": "GEMINI_API_KEY",
        "temperature": 0.7,
        "max_tokens": 2048,
        "tools": ["web_search"],
        "max_iterations": 15,
        "allow_delegation": False,
        "verbose": True,
    }
    renderer.render_to_file("agent.yml.j2", agent_path / "agent.yml", agent_context)

    # Agent handler
    handler_context = {
        "agent_name": agent_name,
        "description": "An example agent that performs research and summarization.",
        "tools": ["web_search"],
    }
    renderer.render_to_file("agent_handler.py.j2", agent_path / "handler.py", handler_context)

    # Web search tool
    renderer.render_to_file("tool_web_search.py.j2", tools_path / "web_search.py", {})

    # Worker
    worker_context = {"agent_name": agent_name}
    renderer.render_to_file(
        "agent_worker.py.j2",
        project_path / "workers" / f"{agent_name}_worker.py",
        worker_context,
    )

    # Update evenage.yml to add agent
    config_path = project_path / "evenage.yml"
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    config_data["project"]["agents"] = [agent_name]

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    # Add worker service to docker-compose.yml
    _add_worker_to_compose(project_path, agent_name)

    # Create example pipeline
    pipeline_context = {
        "pipeline_name": "research_pipeline",
        "description": "Example research pipeline using the researcher agent",
    }
    renderer.render_to_file(
        "pipeline.yml.j2",
        project_path / "pipelines" / "research_pipeline.yml",
        pipeline_context,
    )


def _add_worker_to_compose(project_path: Path, agent_name: str) -> None:
    """Add worker service to docker-compose.yml."""
    compose_path = project_path / "docker-compose.yml"

    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    # Add worker service
    worker_service = {
        "build": ".",
        "command": f"python workers/{agent_name}_worker.py",
        "env_file": ".env",
        "environment": {
            "AGENT_NAME": agent_name,
            "DATABASE_URL": "postgresql://postgres:postgres@postgres:5432/evenage",
            "REDIS_URL": "redis://redis:6379",
            "MINIO_ENDPOINT": "minio:9000",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://jaeger:4318",
        },
        "depends_on": ["redis", "postgres"],
        "volumes": [".:/app"],
        "deploy": {
            "replicas": 1,
            "restart_policy": {
                "condition": "on-failure",
                "delay": "5s",
                "max_attempts": 3,
            },
            "resources": {
                "limits": {"cpus": "1.0", "memory": "1G"},
                "reservations": {"cpus": "0.5", "memory": "512M"},
            },
        },
    }

    compose_data["services"][f"{agent_name}_worker"] = worker_service

    with open(compose_path, "w", encoding="utf-8") as f:
        yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)


def _generate_readme(project_path: Path, project_name: str) -> None:
    """Generate project README."""
    renderer = get_template_renderer()
    renderer.render_to_file(
        "README.md.j2",
        project_path / "README.md",
        {"project_name": project_name},
    )
