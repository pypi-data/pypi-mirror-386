"""
Run command for EvenAge CLI.

Manages Docker environment and job execution.
"""

from __future__ import annotations

import time
from pathlib import Path

import click

from ..utils import (
    ProjectNotFoundError,
    check_docker,
    check_docker_compose,
    compose_up,
    print_info,
    print_panel,
    print_success,
    validate_project_directory,
    wait_for_service,
)


@click.group()
def run():
    """Run environments or jobs."""
    pass


@run.command("dev")
@click.option("--build", is_flag=True, help="Force rebuild images")
@click.option("--detach/--no-detach", default=True, help="Run in detached mode")
def run_dev(build: bool, detach: bool):
    """Run the EvenAge development environment.
    
    Starts all infrastructure services and agent workers:
    - PostgreSQL (with pgvector)
    - Redis
    - MinIO
    - Jaeger (tracing)
    - Prometheus (metrics)
    - API server
    - Agent workers
    - Dashboard
    
    Examples:
        evenage run dev
        evenage run dev --build
        evenage run dev --no-detach  # Follow logs
    """
    # Ensure we're in a project
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    # Check Docker availability
    check_docker()
    check_docker_compose()

    print_panel(
        "Starting EvenAge Development Environment",
        "Building and starting all services...",
    )

    # Start services
    compose_up(detach=detach, build=build)

    if detach:
        # Wait for critical services
        print_info("Waiting for services to be ready...")
        time.sleep(5)

        # Check service health
        critical_services = ["postgres", "redis", "api"]
        for service in critical_services:
            wait_for_service(service, timeout=30)

        print_success("EvenAge is running!")
        _print_service_info()
        _print_management_commands()


def _print_service_info() -> None:
    """Print service URLs."""
    print_panel(
        "Services",
        "[cyan]Dashboard:[/cyan]  http://localhost:5173\n"
        "[cyan]API:[/cyan]        http://localhost:8000\n"
        "[cyan]Jaeger:[/cyan]     http://localhost:16686\n"
        "[cyan]Prometheus:[/cyan] http://localhost:9090\n"
        "[cyan]MinIO:[/cyan]      http://localhost:9001",
        style="green",
    )


def _print_management_commands() -> None:
    """Print management command help."""
    print_panel(
        "Commands",
        "evenage logs <agent>  - View agent logs\n"
        "evenage ps            - Show container status\n"
        "evenage scale <agent> <N> - Scale agent workers\n"
        "evenage stop          - Stop all services",
        style="cyan",
    )


# Alias for backward compatibility
@click.command(name="run-dev", hidden=True)
def run_dev_alias():
    """Alias for 'evenage run dev'."""
    from click import Context

    ctx = Context(run_dev)
    ctx.invoke(run_dev)
