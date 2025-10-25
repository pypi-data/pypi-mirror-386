"""
Docker and Docker Compose utilities for EvenAge CLI.

Provides cross-platform Docker operations with proper error handling.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Optional

from .errors import DockerComposeError, DockerNotFoundError
from .logger import console, print_info, print_success


def check_docker() -> bool:
    """Check if Docker is installed and running.

    Returns:
        True if Docker is available

    Raises:
        DockerNotFoundError: If Docker is not found or not running
    """
    try:
        result = subprocess.run(
            ["docker", "version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode != 0:
            raise DockerNotFoundError()
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        raise DockerNotFoundError()


def check_docker_compose() -> bool:
    """Check if Docker Compose is available.

    Returns:
        True if Docker Compose is available

    Raises:
        DockerNotFoundError: If Docker Compose is not found
    """
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode != 0:
            raise DockerNotFoundError()
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        raise DockerNotFoundError()


def compose_up(
    services: Optional[list[str]] = None,
    detach: bool = True,
    build: bool = False,
    scale: Optional[dict[str, int]] = None,
) -> None:
    """Start Docker Compose services.

    Args:
        services: Optional list of specific services to start
        detach: Run in detached mode (default: True)
        build: Force rebuild images (default: False)
        scale: Optional dict of service: replicas for scaling

    Raises:
        DockerComposeError: If compose up fails
    """
    cmd = ["docker", "compose", "up"]

    if detach:
        cmd.append("-d")

    if build:
        cmd.append("--build")

    if scale:
        for service, replicas in scale.items():
            cmd.extend(["--scale", f"{service}={replicas}"])

    if services:
        cmd.extend(services)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,  # 5 minutes timeout
        )
        if result.returncode != 0:
            raise DockerComposeError("up", result.stderr or result.stdout)
    except subprocess.TimeoutExpired:
        raise DockerComposeError("up", "Operation timed out after 5 minutes")
    except FileNotFoundError:
        raise DockerNotFoundError()


def compose_down(remove_volumes: bool = False) -> None:
    """Stop Docker Compose services.

    Args:
        remove_volumes: Remove named volumes (default: False)

    Raises:
        DockerComposeError: If compose down fails
    """
    cmd = ["docker", "compose", "down"]

    if remove_volumes:
        cmd.append("-v")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if result.returncode != 0:
            raise DockerComposeError("down", result.stderr or result.stdout)
    except subprocess.TimeoutExpired:
        raise DockerComposeError("down", "Operation timed out")
    except FileNotFoundError:
        raise DockerNotFoundError()


def compose_ps(services: Optional[list[str]] = None) -> str:
    """Get status of Docker Compose services.

    Args:
        services: Optional list of specific services to check

    Returns:
        Status output as string

    Raises:
        DockerComposeError: If compose ps fails
    """
    cmd = ["docker", "compose", "ps"]

    if services:
        cmd.extend(services)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode != 0:
            raise DockerComposeError("ps", result.stderr or result.stdout)
        return result.stdout
    except subprocess.TimeoutExpired:
        raise DockerComposeError("ps", "Operation timed out")
    except FileNotFoundError:
        raise DockerNotFoundError()


def compose_logs(
    service: str,
    follow: bool = False,
    tail: Optional[int] = None,
) -> None:
    """View logs for a Docker Compose service.

    Args:
        service: Service name
        follow: Follow log output (default: False)
        tail: Number of lines to show from end (default: all)

    Raises:
        DockerComposeError: If compose logs fails
    """
    cmd = ["docker", "compose", "logs"]

    if follow:
        cmd.append("-f")

    if tail is not None:
        cmd.extend(["--tail", str(tail)])

    cmd.append(service)

    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        raise DockerNotFoundError()
    except KeyboardInterrupt:
        # User stopped following logs
        pass


def compose_scale(service: str, replicas: int) -> None:
    """Scale a Docker Compose service.

    Args:
        service: Service name
        replicas: Number of replicas

    Raises:
        DockerComposeError: If scaling fails
    """
    if replicas < 0:
        raise ValueError("Replicas must be >= 0")

    try:
        result = subprocess.run(
            ["docker", "compose", "up", "--scale", f"{service}={replicas}", "-d"],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        if result.returncode != 0:
            raise DockerComposeError("scale", result.stderr or result.stdout)
    except subprocess.TimeoutExpired:
        raise DockerComposeError("scale", "Operation timed out")
    except FileNotFoundError:
        raise DockerNotFoundError()


def wait_for_service(
    service: str,
    timeout: int = 30,
    check_interval: int = 2,
) -> bool:
    """Wait for a service to be healthy.

    Args:
        service: Service name
        timeout: Maximum seconds to wait
        check_interval: Seconds between checks

    Returns:
        True if service is healthy, False otherwise
    """
    print_info(f"Waiting for {service} to be ready...")

    elapsed = 0
    while elapsed < timeout:
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json", service],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if result.returncode == 0 and "running" in result.stdout.lower():
                print_success(f"{service} is ready")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        time.sleep(check_interval)
        elapsed += check_interval

    return False


def build_image(dockerfile: Path, tag: str, context: Path) -> None:
    """Build a Docker image.

    Args:
        dockerfile: Path to Dockerfile
        tag: Image tag
        context: Build context directory

    Raises:
        DockerComposeError: If build fails
    """
    try:
        result = subprocess.run(
            ["docker", "build", "-f", str(dockerfile), "-t", tag, str(context)],
            capture_output=True,
            text=True,
            check=False,
            timeout=600,  # 10 minutes
        )
        if result.returncode != 0:
            raise DockerComposeError("build", result.stderr or result.stdout)
    except subprocess.TimeoutExpired:
        raise DockerComposeError("build", "Build timed out after 10 minutes")
    except FileNotFoundError:
        raise DockerNotFoundError()
