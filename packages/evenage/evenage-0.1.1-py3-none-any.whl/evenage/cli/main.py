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
@click.version_option(version="0.1.1")
def cli():
    """EvenAge - Transparent, Docker-native agent framework."""
    pass


# --- Helpers (shared logic) ---

def _create_agent_files(agent_name: str, non_interactive: bool = False):
    """Create agent YAML and update project config and compose."""
    # Ensure project
    if not Path("evenage.yml").exists():
        console.print("[red]Error: Not in an EvenAge project directory[/red]")
        sys.exit(1)

    console.print(f"[bold]Adding agent:[/bold] {agent_name}")

    # Create agent directory
    agent_path = Path("agents") / agent_name
    agent_path.mkdir(parents=True, exist_ok=True)

    if non_interactive:
        role = "Research Agent"
        goal = "Research topics on the web and summarize findings concisely."
        backstory = "A helpful researcher that gathers and condenses information from reliable web sources."
        llm_config = {
            "provider": "gemini",
            "model": "gemini-2.0-flash-exp",
            "api_key": "${GEMINI_API_KEY}",  # User must set in .env
            "temperature": 0.7,
            "max_tokens": 2048
        }
        tools = ["web_search"]
    else:
        role = click.prompt("Role")
        goal = click.prompt("Goal")
        backstory = click.prompt("Backstory", default="", show_default=False)
        llm_model = click.prompt("LLM model", default="gpt-4")
        llm_config = llm_model  # keep CLI simple: string model maps to OpenAI by default
        tools = []

    # Create agent.yml
    agent_config = {
        "name": agent_name,
        "role": role,
        "goal": goal,
        "backstory": backstory if backstory else None,
        "llm": llm_config,
        "tools": tools,
        "max_iterations": 15,
        "allow_delegation": False,
        "verbose": True,
    }

    with open(agent_path / "agent.yml", "w") as f:
        yaml.dump(agent_config, f, default_flow_style=False, sort_keys=False)

    # Update evenage.yml
    with open("evenage.yml") as f:
        project_config = yaml.safe_load(f)

    if agent_name not in project_config["project"].get("agents", []):
        project_config["project"].setdefault("agents", []).append(agent_name)

    with open("evenage.yml", "w") as f:
        yaml.dump(project_config, f, default_flow_style=False, sort_keys=False)

    # Update docker-compose.yml to add worker
    add_agent_to_docker_compose(agent_name)

    console.print(f"[green]✓[/green] Agent {agent_name} created")
    console.print(f"  Config: agents/{agent_name}/agent.yml")
    console.print(f"  Worker service added to docker-compose.yml")


def _create_tool_file(tool_name: str, non_interactive: bool = False):
    # Ensure project
    if not Path("evenage.yml").exists():
        console.print("[red]Error: Not in an EvenAge project directory[/red]")
        sys.exit(1)

    console.print(f"[bold]Adding tool:[/bold] {tool_name}")

    tool_path = Path("tools") / f"{tool_name}.py"

    # Simple web_search default tool for demo
    if non_interactive and tool_name == "web_search":
        tool_template = '''"""
web_search tool for EvenAge agents.

Uses Serper.dev API for real web search results.
"""
from typing import Any
import os
import json


def web_search(query: str = "", max_results: int = 5, **kwargs: Any) -> str:
    """
    Search the web using Serper.dev API.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)
        **kwargs: Additional parameters

    Returns:
        Formatted search results as a string

    Environment:
        SERPER_API_KEY: Your Serper.dev API key (get from https://serper.dev)
    """
    api_key = os.getenv("SERPER_API_KEY")
    
    if not api_key:
        return (
            "Error: SERPER_API_KEY not set. "
            "Get your API key from https://serper.dev and add it to .env"
        )
    
    try:
        import requests
        
        url = "https://google.serper.dev/search"
        payload = json.dumps({
            "q": query,
            "num": max_results
        })
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Format results
        results = []
        if "organic" in data:
            for idx, item in enumerate(data["organic"][:max_results], 1):
                title = item.get("title", "")
                link = item.get("link", "")
                snippet = item.get("snippet", "")
                results.append(f"{idx}. {title}\\n   {snippet}\\n   {link}")
        
        if not results:
            return f"No results found for query: {query}"
        
        return "\\n\\n".join(results)
        
    except ImportError:
        return "Error: requests library not installed. Run: pip install requests"
    except Exception as e:
        return f"Error searching web: {str(e)}"
'''
    else:
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


def _create_skeleton_pipeline():
    """Create a skeleton pipeline YAML for demo purposes."""
    pipeline_path = Path("pipelines") / "research_pipeline.yml"
    
    pipeline_config = {
        "name": "research_pipeline",
        "description": "Example research pipeline using the researcher agent",
        "tasks": [
            {
                "name": "search_topic",
                "description": "Search the web for information about: {topic}",
                "agent": "researcher",
                "expected_output": "A comprehensive summary of web search results",
                "tools": ["web_search"],
                "async_execution": False
            },
            {
                "name": "analyze_results",
                "description": "Analyze the search results and extract key insights",
                "agent": "researcher",
                "expected_output": "Key insights and recommendations based on the research",
                "context": ["search_topic"],
                "async_execution": False
            }
        ]
    }
    
    with open(pipeline_path, "w") as f:
        yaml.dump(pipeline_config, f, default_flow_style=False, sort_keys=False)
    
    console.print(f"[green]✓[/green] Skeleton pipeline created: {pipeline_path}")


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
            project_path / "docker",  # for prometheus and other service configs
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
            yaml.dump(project_config, f, default_flow_style=False, sort_keys=False)

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

# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Tool API Keys
SERPER_API_KEY=your_serper_api_key_here
"""
        with open(project_path / ".env", "w") as f:
            f.write(env_content)

        # Create Prometheus config (required by prometheus image)
        prometheus_config = """global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'evenage-api'
    static_configs:
      - targets: ['api:8001']
"""
        (project_path / "docker").mkdir(parents=True, exist_ok=True)
        with open(project_path / "docker/prometheus.yml", "w") as f:
            f.write(prometheus_config)

        # Create docker-compose.yml
        progress.update(task, description="Creating Docker configuration...")
        create_docker_compose(project_path, project_name)

        # Create Dockerfile
        create_dockerfile(project_path)

        # Seed default tool and agent
        progress.update(task, description="Seeding default agent and tool...")
        _cwd = os.getcwd()
        try:
            os.chdir(project_path)
            _create_tool_file("web_search", non_interactive=True)
            _create_agent_files("researcher", non_interactive=True)
            _create_skeleton_pipeline()
        finally:
            os.chdir(_cwd)

        # Create README
        progress.update(task, description="Creating README...")
        create_readme(project_path, project_name)

    console.print(f"\n[green]✓[/green] Project created: {project_path}")
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  cd {project_name}")
    console.print("  evenage run dev")


# New UX: `evenage add agent|tool` group
@cli.group("add")
def add_group():
    """Add resources to your project (agents, tools)."""
    pass


@add_group.command("agent")
@click.argument("agent_name")
def add_group_agent(agent_name: str):
    _create_agent_files(agent_name, non_interactive=False)


@add_group.command("tool")
@click.argument("tool_name")
def add_group_tool(tool_name: str):
    _create_tool_file(tool_name, non_interactive=False)


# Back-compat legacy commands: evenage add-agent / add-tool
@cli.command(name="add-agent", hidden=True)
@click.argument("agent_name")
def add_agent(agent_name: str):
    """Add a new agent to the project (legacy)."""
    _create_agent_files(agent_name, non_interactive=False)


@cli.command(name="add-tool", hidden=True)
@click.argument("tool_name")
def add_tool(tool_name: str):
    """Add a new custom tool to the project (legacy)."""
    _create_tool_file(tool_name, non_interactive=False)


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
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (from requirements.txt)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (project files mounted in dev via volumes)
COPY . .

CMD ["python", "-m", "evenage.api.main"]
"""

    with open(project_path / "Dockerfile", "w") as f:
        f.write(dockerfile_content)

    # Create requirements.txt (add Gemini and requests for web_search tool)
    requirements = """evenage==0.1.0
requests>=2.31.0
google-generativeai>=0.3.0
"""

    with open(project_path / "requirements.txt", "w") as f:
        f.write(requirements)


def create_readme(project_path: Path, project_name: str):
    """Create README.md."""
    readme_content = f"""# {project_name}

An EvenAge agent project.

## Getting Started

1) Initialize (already done)

2) Run the environment

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
- A default agent worker (researcher)
- Dashboard (pulled from Docker Hub)

### Access services

- Dashboard: http://localhost:5173
- API: http://localhost:8000
- Jaeger: http://localhost:16686
- Prometheus: http://localhost:9090
- MinIO: http://localhost:9001

### Add more

- `evenage add agent <name>` - Add a new agent
- `evenage add tool <name>` - Add a custom tool
- `evenage logs <agent>` - View agent logs
- `evenage stop` - Stop all services

## Project Structure

```
{project_name}/
├── evenage.yml          # Project configuration
├── docker-compose.yml   # Docker services
├── agents/              # Agent configurations (default: researcher)
├── tools/               # Custom tools (default: web_search)
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
            "replicas": 1,
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
