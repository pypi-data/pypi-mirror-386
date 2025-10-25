"""
Add command for EvenAge CLI.

Adds agents and tools to existing projects.
"""

from __future__ import annotations

from pathlib import Path

import click
import yaml

from ..utils import (
    AgentNotFoundError,
    ProjectNotFoundError,
    get_template_renderer,
    print_info,
    print_success,
    validate_project_directory,
    write_file,
)


@click.group()
def add():
    """Add resources to your project (agents, tools)."""
    pass


@add.command("agent")
@click.argument("agent_name")
@click.option("--role", help="Agent role")
@click.option("--goal", help="Agent goal")
@click.option("--backstory", help="Agent backstory")
@click.option("--llm-provider", default="gemini", help="LLM provider")
@click.option("--llm-model", default="gemini-2.0-flash-exp", help="LLM model")
def add_agent(
    agent_name: str,
    role: str | None,
    goal: str | None,
    backstory: str | None,
    llm_provider: str,
    llm_model: str,
):
    """Add a new agent to the project.
    
    Examples:
        evenage add agent summarizer
        evenage add agent analyst --role "Data Analyst" --goal "Analyze data"
    """
    # Ensure we're in a project
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    print_info(f"Adding agent: {agent_name}")

    # Prompt for missing details
    if not role:
        role = click.prompt("Agent role")
    if not goal:
        goal = click.prompt("Agent goal")
    if not backstory:
        backstory = click.prompt("Agent backstory", default="", show_default=False)

    # Create agent files
    _create_agent_files(
        agent_name=agent_name,
        role=role,
        goal=goal,
        backstory=backstory,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )

    print_success(f"Agent {agent_name} created")
    print_info(f"  Config: agents/{agent_name}/agent.yml")
    print_info(f"  Handler: agents/{agent_name}/handler.py")
    print_info(f"  Worker: workers/{agent_name}_worker.py")
    print_info(f"  Docker service added to docker-compose.yml")


@add.command("tool")
@click.argument("tool_name")
@click.option("--agent", help="Agent to attach tool to (default: first agent)")
@click.option("--description", help="Tool description")
def add_tool(
    tool_name: str,
    agent: str | None,
    description: str | None,
):
    """Add a new tool to an agent.
    
    Examples:
        evenage add tool calculator
        evenage add tool scraper --agent researcher
    """
    # Ensure we're in a project
    if not validate_project_directory(Path.cwd()):
        raise ProjectNotFoundError()

    print_info(f"Adding tool: {tool_name}")

    # Determine target agent
    if not agent:
        with open("evenage.yml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        agents = config.get("project", {}).get("agents", [])
        if not agents:
            raise AgentNotFoundError("No agents found in project")
        agent = agents[0]
        print_info(f"Attaching to agent: {agent}")

    # Prompt for description if not provided
    if not description:
        description = click.prompt("Tool description", default=f"{tool_name} tool")

    # Create tool file
    _create_tool_file(tool_name, agent, description)

    print_success(f"Tool {tool_name} created")
    print_info(f"  File: agents/{agent}/tools/{tool_name}.py")
    print_info(f"  Added to {agent} agent configuration")


def _create_agent_files(
    agent_name: str,
    role: str,
    goal: str,
    backstory: str,
    llm_provider: str,
    llm_model: str,
) -> None:
    """Create agent files and update configuration."""
    renderer = get_template_renderer()

    # Create agent directory structure
    agent_path = Path("agents") / agent_name
    tools_path = agent_path / "tools"
    agent_path.mkdir(parents=True, exist_ok=True)
    tools_path.mkdir(parents=True, exist_ok=True)

    # __init__ files
    write_file(agent_path / "__init__.py", "")
    write_file(tools_path / "__init__.py", "")

    # Determine API key env var based on provider
    api_key_vars = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
    }
    llm_api_key_var = api_key_vars.get(llm_provider.lower(), f"{llm_provider.upper()}_API_KEY")

    # Agent configuration
    agent_context = {
        "agent_name": agent_name,
        "role": role,
        "goal": goal,
        "backstory": backstory if backstory else None,
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "llm_api_key_var": llm_api_key_var,
        "temperature": 0.7,
        "max_tokens": 2048,
        "tools": [],
        "max_iterations": 15,
        "allow_delegation": False,
        "verbose": True,
    }
    renderer.render_to_file("agent.yml.j2", agent_path / "agent.yml", agent_context)

    # Agent handler
    handler_context = {
        "agent_name": agent_name,
        "description": role,
        "tools": [],
    }
    renderer.render_to_file("agent_handler.py.j2", agent_path / "handler.py", handler_context)

    # Worker
    worker_context = {"agent_name": agent_name}
    renderer.render_to_file(
        "agent_worker.py.j2",
        Path("workers") / f"{agent_name}_worker.py",
        worker_context,
    )

    # Update evenage.yml
    with open("evenage.yml", "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    if agent_name not in config_data["project"].get("agents", []):
        config_data["project"].setdefault("agents", []).append(agent_name)

    with open("evenage.yml", "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    # Add worker service to docker-compose.yml
    _add_worker_to_compose(agent_name)


def _create_tool_file(tool_name: str, agent_name: str, description: str) -> None:
    """Create tool file and update agent configuration."""
    renderer = get_template_renderer()

    # Create tool file
    tools_dir = Path("agents") / agent_name / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    tool_context = {
        "tool_name": tool_name,
        "description": description,
    }
    renderer.render_to_file("tool.py.j2", tools_dir / f"{tool_name}.py", tool_context)

    # Update agent.yml to add tool
    agent_yml = Path("agents") / agent_name / "agent.yml"
    with open(agent_yml, "r", encoding="utf-8") as f:
        agent_config = yaml.safe_load(f)

    tools_list = agent_config.get("tools", []) or []
    if tool_name not in tools_list:
        tools_list.append(tool_name)
        agent_config["tools"] = tools_list

    with open(agent_yml, "w", encoding="utf-8") as f:
        yaml.dump(agent_config, f, default_flow_style=False, sort_keys=False)


def _add_worker_to_compose(agent_name: str) -> None:
    """Add worker service to docker-compose.yml."""
    compose_path = Path("docker-compose.yml")

    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    # Check if service already exists
    if f"{agent_name}_worker" in compose_data.get("services", {}):
        return

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

    compose_data.setdefault("services", {})[f"{agent_name}_worker"] = worker_service

    with open(compose_path, "w", encoding="utf-8") as f:
        yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)
