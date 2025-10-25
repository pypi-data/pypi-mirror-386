"""
EvenAge CLI - Command-line interface for managing EvenAge projects.

Provides commands for:
- Initializing new projects
- Adding agents and tools
- Running Docker environment
- Managing jobs
- Viewing logs
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """EvenAge - Transparent, Docker-native agent framework."""
    pass


@cli.command()
@click.argument("project_name", required=False)
@click.option("--path", default=".", help="Path to create project in")
def init(project_name: str | None, path: str):
    """Initialize a new EvenAge project."""
    if not project_name:
        project_name = click.prompt("Project name")

    project_path = Path(path) / project_name
    if project_path.exists():
        console.print(f"[red]Error: Directory {project_path} already exists[/red]")
        sys.exit(1)

    console.print(Panel(f"Initializing EvenAge project: [bold]{project_name}[/bold]"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating project structure...", total=None)

        # Create directory structure
        directories = [
            project_path,
            project_path / "agents",
            project_path / "tools",
            project_path / "pipelines",
        ]

        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create evenage.yml
        project_config = {
            "project": {
                "name": project_name,
                "broker": "redis",
                "database": "postgres",
                "storage": "minio",
                "tracing": True,
                "metrics": True,
                "agents": [],
            }
        }

        with open(project_path / "evenage.yml", "w") as f:
            yaml.dump(project_config, f, default_flow_style=False)

        # Create .env file
        env_content = """# EvenAge Environment Configuration
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/evenage
REDIS_URL=redis://redis:6379
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_SECURE=false
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318
API_HOST=0.0.0.0
API_PORT=8000
PROMETHEUS_METRICS_PORT=8001

# Dashboard Authentication (format: "username1:password1,username2:password2")
EVENAGE_DASH_USERS=admin:admin
"""
        with open(project_path / ".env", "w") as f:
            f.write(env_content)

        # Create docker-compose.yml
        progress.update(task, description="Creating Docker configuration...")
        create_docker_compose(project_path, project_name)

        # Create Dockerfile
        create_dockerfile(project_path)

        # Create README
        progress.update(task, description="Creating README...")
        create_readme(project_path, project_name)

    console.print(f"\n[green]✓[/green] Project created: {project_path}")
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  cd {project_name}")
    console.print("  evenage add agent <agent_name>")
    console.print("  evenage run dev")


@cli.command()
@click.argument("agent_name")
def add_agent(agent_name: str):
    """Add a new agent to the project."""
    # Check if we're in an EvenAge project
    if not Path("evenage.yml").exists():
        console.print("[red]Error: Not in an EvenAge project directory[/red]")
        sys.exit(1)

    console.print(f"[bold]Adding agent:[/bold] {agent_name}")

    # Create agent directory
    agent_path = Path("agents") / agent_name
    agent_path.mkdir(parents=True, exist_ok=True)

    # Prompt for agent details
    role = click.prompt("Role")
    goal = click.prompt("Goal")
    backstory = click.prompt("Backstory", default="", show_default=False)
    llm = click.prompt("LLM model", default="gpt-4")

    # Create agent.yml
    agent_config = {
        "name": agent_name,
        "role": role,
        "goal": goal,
        "backstory": backstory if backstory else None,
        "llm": llm,
        "tools": [],
        "max_iterations": 15,
        "allow_delegation": False,
        "verbose": True,
    }

    with open(agent_path / "agent.yml", "w") as f:
        yaml.dump(agent_config, f, default_flow_style=False)

    # Update evenage.yml
    with open("evenage.yml") as f:
        project_config = yaml.safe_load(f)

    if agent_name not in project_config["project"]["agents"]:
        project_config["project"]["agents"].append(agent_name)

    with open("evenage.yml", "w") as f:
        yaml.dump(project_config, f, default_flow_style=False)

    # Update docker-compose.yml to add worker
    add_agent_to_docker_compose(agent_name)

    console.print(f"[green]✓[/green] Agent {agent_name} created")
    console.print(f"  Config: agents/{agent_name}/agent.yml")
    console.print(f"  Worker service added to docker-compose.yml")


@cli.command()
@click.argument("tool_name")
def add_tool(tool_name: str):
    """Add a new custom tool to the project."""
    # Check if we're in an EvenAge project
    if not Path("evenage.yml").exists():
        console.print("[red]Error: Not in an EvenAge project directory[/red]")
        sys.exit(1)

    console.print(f"[bold]Adding tool:[/bold] {tool_name}")

    # Create tool file
    tool_path = Path("tools") / f"{tool_name}.py"

    tool_template = f'''"""
{tool_name} tool for EvenAge agents.
"""

from typing import Any


def {tool_name}(**kwargs: Any) -> str:
    """
    TODO: Implement tool logic.

    Args:
        **kwargs: Tool parameters

    Returns:
        Tool result
    """
    return "Tool result"
'''

    with open(tool_path, "w") as f:
        f.write(tool_template)

    console.print(f"[green]✓[/green] Tool created: {tool_path}")


@cli.command()
def run_dev():
    """Run the EvenAge development environment."""
    # Check if we're in an EvenAge project
    if not Path("evenage.yml").exists():
        console.print("[red]Error: Not in an EvenAge project directory[/red]")
        sys.exit(1)

    console.print(Panel("[bold]Starting EvenAge Development Environment[/bold]"))

    try:
        # Run docker compose up
        console.print("\n[bold]Building and starting containers...[/bold]")
        subprocess.run(
            ["docker", "compose", "up", "-d", "--build"],
            check=True,
        )

        # Wait for services to be healthy
        console.print("\n[bold]Waiting for services to be ready...[/bold]")
        time.sleep(5)

        # Show status
        console.print("\n[green]✓[/green] EvenAge is running!")
        console.print("\n[bold]Services:[/bold]")
        console.print("  [cyan]Dashboard:[/cyan]  http://localhost:5173  [dim](Full observability UI)[/dim]")
        console.print("  [cyan]API:[/cyan]        http://localhost:8000  [dim](REST + WebSocket)[/dim]")
        console.print("  [cyan]Jaeger:[/cyan]     http://localhost:16686 [dim](Distributed tracing)[/dim]")
        console.print("  [cyan]Prometheus:[/cyan] http://localhost:9090  [dim](Metrics)[/dim]")
        console.print("  [cyan]MinIO:[/cyan]      http://localhost:9001  [dim](Object storage)[/dim]")
        console.print("\n[bold]Commands:[/bold]")
        console.print("  evenage logs <agent>  - View agent logs")
        console.print("  evenage ps            - Show container status")
        console.print("  evenage stop          - Stop all services")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error starting services: {e}[/red]")
        sys.exit(1)
    except FileNotFoundError:
        console.print("[red]Error: Docker not found. Please install Docker.[/red]")
        sys.exit(1)


@cli.command()
@click.argument("agent_name")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def logs(agent_name: str, follow: bool):
    """View logs for an agent."""
    try:
        cmd = ["docker", "compose", "logs"]
        if follow:
            cmd.append("-f")
        cmd.append(f"{agent_name}_worker")

        subprocess.run(cmd)

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error viewing logs: {e}[/red]")
        sys.exit(1)


@cli.command()
def stop():
    """Stop all EvenAge services."""
    # Check if we're in an EvenAge project
    if not Path("evenage.yml").exists():
        console.print("[red]Error: Not in an EvenAge project directory[/red]")
        sys.exit(1)

    console.print("[bold]Stopping EvenAge services...[/bold]")

    try:
        subprocess.run(["docker", "compose", "down"], check=True)
        console.print("[green]✓[/green] Services stopped")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error stopping services: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("agent_name")
@click.argument("replicas", type=int)
def scale(agent_name: str, replicas: int):
    """Scale an agent worker to N replicas.
    
    Example: evenage scale researcher 3
    """
    # Check if we're in an EvenAge project
    if not Path("evenage.yml").exists():
        console.print("[red]Error: Not in an EvenAge project directory[/red]")
        sys.exit(1)
    
    if replicas < 0:
        console.print("[red]Error: Replicas must be >= 0[/red]")
        sys.exit(1)
    
    console.print(f"[bold]Scaling {agent_name} worker to {replicas} replicas...[/bold]")
    
    try:
        subprocess.run(
            ["docker", "compose", "up", "--scale", f"{agent_name}_worker={replicas}", "-d"],
            check=True
        )
        console.print(f"[green]✓[/green] {agent_name} scaled to {replicas} instances")
        
        # Show container status
        subprocess.run(["docker", "compose", "ps", f"{agent_name}_worker"])
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error scaling worker: {e}[/red]")
        sys.exit(1)


@cli.command()
def ps():
    """Show status of all services and workers."""
    # Check if we're in an EvenAge project
    if not Path("evenage.yml").exists():
        console.print("[red]Error: Not in an EvenAge project directory[/red]")
        sys.exit(1)
    
    console.print("[bold]EvenAge Services Status:[/bold]\n")
    
    try:
        subprocess.run(["docker", "compose", "ps"])
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("pipeline_file")
@click.option("--input", "-i", multiple=True, help="Input variables (key=value)")
def run_job(pipeline_file: str, input: tuple):
    """Run a job from a pipeline file."""
    # Parse inputs
    inputs = {}
    for item in input:
        if "=" not in item:
            console.print(f"[red]Invalid input format: {item}[/red]")
            sys.exit(1)
        key, value = item.split("=", 1)
        inputs[key] = value

    console.print(f"[bold]Submitting job:[/bold] {pipeline_file}")
    console.print(f"[bold]Inputs:[/bold] {inputs}")

    # TODO: Implement API call to submit job
    console.print("[yellow]Job submission not yet implemented[/yellow]")


def create_docker_compose(project_path: Path, project_name: str):
    """Create docker-compose.yml file."""
    compose_config = {
        "version": "3.9",
        "services": {
            "postgres": {
                "image": "pgvector/pgvector:pg15",
                "environment": {
                    "POSTGRES_DB": "evenage",
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_PASSWORD": "postgres",
                },
                "ports": ["5432:5432"],
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
            },
            "redis": {
                "image": "redis:7-alpine",
                "ports": ["6379:6379"],
            },
            "minio": {
                "image": "minio/minio",
                "environment": {
                    "MINIO_ROOT_USER": "minioadmin",
                    "MINIO_ROOT_PASSWORD": "minioadmin123",
                },
                "command": 'server /data --console-address ":9001"',
                "ports": ["9000:9000", "9001:9001"],
                "volumes": ["minio_data:/data"],
            },
            "jaeger": {
                "image": "jaegertracing/all-in-one:latest",
                "ports": ["16686:16686", "4318:4318"],
            },
            "prometheus": {
                "image": "prom/prometheus:latest",
                "ports": ["9090:9090"],
                "volumes": ["./docker/prometheus.yml:/etc/prometheus/prometheus.yml"],
            },
            "dashboard": {
                "image": "nishantgupt786/dashboard:latest",
                "ports": ["5173:5173"],
                "environment": {
                    "VITE_API_URL": "http://api:8000",
                    "VITE_DASH_USERS": "${EVENAGE_DASH_USERS:-admin:admin}",
                },
                "depends_on": ["api"],
                "healthcheck": {
                    "test": ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:5173/"],
                    "interval": "30s",
                    "timeout": "3s",
                    "start_period": "5s",
                    "retries": 3,
                },
            },
            "api": {
                "build": ".",
                "command": "python -m evenage.api.main",
                "ports": ["8000:8000"],
                "environment": {
                    "DATABASE_URL": "postgresql://postgres:postgres@postgres:5432/evenage",
                    "REDIS_URL": "redis://redis:6379",
                    "MINIO_ENDPOINT": "minio:9000",
                    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://jaeger:4318",
                },
                "depends_on": ["postgres", "redis", "minio", "jaeger"],
                "volumes": [".:/app"],
            },
        },
        "volumes": {
            "postgres_data": None,
            "minio_data": None,
        },
    }

    with open(project_path / "docker-compose.yml", "w") as f:
        yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)


def create_dockerfile(project_path: Path):
    """Create Dockerfile."""
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install evenage package
RUN pip install -e .

CMD ["python", "-m", "evenage.api.main"]
"""

    with open(project_path / "Dockerfile", "w") as f:
        f.write(dockerfile_content)

    # Create requirements.txt
    requirements = """evenage>=0.1.0
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
redis>=5.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
minio>=7.2.0
opentelemetry-api>=1.30.0
opentelemetry-sdk>=1.30.0
opentelemetry-exporter-otlp-proto-http>=1.30.0
prometheus-client>=0.21.0
click>=8.1.7
rich>=13.7.0
pyyaml>=6.0.1
"""

    with open(project_path / "requirements.txt", "w") as f:
        f.write(requirements)


def create_readme(project_path: Path, project_name: str):
    """Create README.md."""
    readme_content = f"""# {project_name}

An EvenAge agent project.

## Getting Started

### 1. Add agents

```bash
evenage add agent summarizer
evenage add agent analyzer
```

### 2. Run the environment

```bash
evenage run dev
```

This will start:
- PostgreSQL (with pgvector)
- Redis
- MinIO
- Jaeger (tracing)
- Prometheus (metrics)
- API server
- Agent workers
- Dashboard (pulled from Docker Hub)

### 3. Access services

- Dashboard: http://localhost:5173
- API: http://localhost:8000
- Jaeger: http://localhost:16686
- Prometheus: http://localhost:9090
- MinIO: http://localhost:9001

## Commands

- `evenage add agent <name>` - Add a new agent
- `evenage add tool <name>` - Add a custom tool
- `evenage run dev` - Start development environment
- `evenage logs <agent>` - View agent logs
- `evenage stop` - Stop all services

## Project Structure

```
{project_name}/
├── evenage.yml          # Project configuration
├── docker-compose.yml   # Docker services
├── agents/              # Agent configurations
├── tools/               # Custom tools
└── pipelines/           # Pipeline definitions
```
"""

    with open(project_path / "README.md", "w") as f:
        f.write(readme_content)


def add_agent_to_docker_compose(agent_name: str):
    """Add a worker service to docker-compose.yml for a new agent with scaling support."""
    with open("docker-compose.yml") as f:
        compose_config = yaml.safe_load(f)

    # Add worker service with deploy configuration for scaling
    worker_service = {
        "build": ".",
        "command": f"python -m evenage.worker.main",
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
            "replicas": 1,  # Default to 1 instance, scale with: docker compose up --scale agent_worker=N
            "restart_policy": {
                "condition": "on-failure",
                "delay": "5s",
                "max_attempts": 3,
            },
            "resources": {
                "limits": {
                    "cpus": "1.0",
                    "memory": "1G",
                },
                "reservations": {
                    "cpus": "0.5",
                    "memory": "512M",
                },
            },
        },
    }

    compose_config["services"][f"{agent_name}_worker"] = worker_service

    with open("docker-compose.yml", "w") as f:
        yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)
    
    console.print(f"\n[bold cyan]Scaling Instructions:[/bold cyan]")
    console.print(f"To scale {agent_name} workers:")
    console.print(f"  docker compose up --scale {agent_name}_worker=3 -d")
    console.print(f"  # This will create 3 instances of the {agent_name} worker")


if __name__ == "__main__":
    cli()
