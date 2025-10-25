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
import importlib
import inspect

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@click.group()
@click.version_option(version="0.1.7")
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

    # Also generate transparent handler/tools and worker runner for this agent
    try:
        _generate_agent(Path("."), agent_name)
        console.print(f"  Code: agents/{agent_name}/handler.py, workers/{agent_name}_worker.py")
    except Exception as e:
        console.log(f"[yellow]Warning:[/yellow] Unable to generate agent code for {agent_name}: {e}")


def _create_tool_file(tool_name: str, non_interactive: bool = False):
    # Ensure project
    if not Path("evenage.yml").exists():
        console.print("[red]Error: Not in an EvenAge project directory[/red]")
        sys.exit(1)

    console.print(f"[bold]Adding tool:[/bold] {tool_name}")

    # Determine target agent to attach the tool to (default: first configured agent)
    with open("evenage.yml") as f:
        project_config = yaml.safe_load(f)
    agents = project_config.get("project", {}).get("agents", [])
    if not agents:
        console.print("[red]No agents found in project. Create an agent first: evenage add agent <name>[/red]")
        sys.exit(1)
    target_agent = agents[0]

    tools_dir = Path("agents") / target_agent / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    tool_path = tools_dir / f"{tool_name}.py"

    # Simple web_search default tool for demo
    if non_interactive and tool_name == "web_search":
        tool_template = '''"""
web_search tool for EvenAge agents.

Uses Serper.dev API for real web search results.
"""
from typing import Any
import os
import json


def run(params: dict[str, Any] | None = None) -> str:
    """
    Search the web using Serper.dev API.

    Params:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)

    Environment:
        SERPER_API_KEY: Your Serper.dev API key (get from https://serper.dev)
    """
    params = params or {}
    query = params.get("query", "")
    max_results = int(params.get("max_results", 5))
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
            for idx, item in enumerate(data.get("organic", [])[:max_results], 1):
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


def run(params: dict[str, Any] | None = None) -> str:
    """
    TODO: Implement tool logic.

    Returns:
        Tool result
    """
    return "Tool result"
'''

    with open(tool_path, "w") as f:
        f.write(tool_template)

    # Append tool to agent.yml tools list if not present
    agent_yml = Path("agents") / target_agent / "agent.yml"
    with open(agent_yml) as f:
        agent_cfg = yaml.safe_load(f)
    tools_list = agent_cfg.get("tools", []) or []
    if tool_name not in tools_list:
        tools_list.append(tool_name)
        agent_cfg["tools"] = tools_list
        with open(agent_yml, "w") as f:
            yaml.dump(agent_cfg, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]✓[/green] Tool created: {tool_path} (attached to agent: {target_agent})")


def _copy_module_source(module_name: str, dest_dir: Path, dest_filename: str | None = None) -> None:
    """Copy the readable source of a Python module into the project for transparency.

    Tries to locate the module's source file via importlib/inspect and writes it under dest_dir.
    """
    try:
        module = importlib.import_module(module_name)
        source_file = inspect.getsourcefile(module)
        if not source_file:
            return
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_name = dest_filename or Path(source_file).name
        with open(source_file, "r") as src, open(dest_dir / out_name, "w") as dst:
            header = (
                f"# NOTE: This is a mirrored copy of {module_name} for transparency.\n"
                "# Edits here do not affect the installed package runtime.\n"
                "# To customize behavior, create your own modules and import them in your workers.\n\n"
            )
            dst.write(header)
            dst.write(src.read())
    except Exception as e:
        # Non-fatal; transparency files are best-effort
        console.log(f"[yellow]Warning:[/yellow] Unable to copy source for {module_name}: {e}")


def _seed_runtime_sources(project_root: Path) -> None:
    """Seed readable runtime sources (agent, message bus, DB, observability) into the project."""
    runtime_dir = project_root / "runtime"
    modules = [
        ("evenage.core.agent", "agent.py"),
        ("evenage.core.message_bus", "message_bus.py"),
        ("evenage.database.models", "database_models.py"),
        ("evenage.observability.metrics", "metrics.py"),
        ("evenage.observability.tracing", "tracing.py"),
    ]
    for mod, name in modules:
        _copy_module_source(mod, runtime_dir, name)


def _write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _generate_transparent_core(project_root: Path):
    """Generate transparent core modules directly into the project."""
    # core/__init__.py
    _write_file(project_root / "core" / "__init__.py", "")

    # core/message_bus.py
    _write_file(project_root / "core" / "message_bus.py", '''import json
import threading
from typing import Callable

import redis


class MessageBus:
    """Redis-based communication layer between agents."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.StrictRedis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis.pubsub()

    def publish(self, channel: str, message: dict):
        data = json.dumps(message)
        self.redis.publish(channel, data)

    def subscribe(self, channel: str, callback: Callable[[dict], None]):
        def listener():
            self.pubsub.subscribe(channel)
            for msg in self.pubsub.listen():
                if msg.get("type") == "message":
                    try:
                        callback(json.loads(msg.get("data", "{}")))
                    except Exception:
                        # swallow callback errors to keep listener alive
                        pass
        thread = threading.Thread(target=listener, daemon=True)
        thread.start()
''')

    # core/agent.py
    _write_file(project_root / "core" / "agent.py", '''from __future__ import annotations
from typing import Any, Callable

from .message_bus import MessageBus


class BaseAgent:
    def __init__(self, config: Any, llm: Any, tools: dict[str, Callable]):
        self.config = config
        self.llm = llm
        self.tools = tools or {}
        self.bus = MessageBus(getattr(config, "redis_url", "redis://localhost:6379"))

    def run_tool(self, tool_name: str, params: dict | None = None) -> Any:
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        return tool(params or {})

    def delegate(self, target_agent: str, data: dict):
        self.bus.publish(f"agent:{target_agent}", {"sender": getattr(self.config, "name", "unknown"), "payload": data})

    def listen(self):
        def on_message(msg: dict):
            result = self.handle(msg)
            self.bus.publish("agent:controller", result)
        self.bus.subscribe(f"agent:{getattr(self.config, 'name', 'unknown')}", on_message)

    def handle(self, task: dict):  # pragma: no cover - to be overridden by concrete agents
        raise NotImplementedError("Agents must implement handle(task)")
''')

    # core/llm.py (minimal local LLM wrapper)
    _write_file(project_root / "core" / "llm.py", '''from __future__ import annotations
import os


class SimpleLLM:
    """Minimal LLM wrapper using Google Generative AI if available, otherwise echo."""

    def __init__(self):
        self._model = None
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel("gemini-2.0-flash-exp")
            except Exception:
                self._model = None

    def chat(self, prompt: str) -> str:
        if self._model:
            try:
                resp = self._model.generate_content(prompt)
                return getattr(resp, "text", str(resp))
            except Exception as e:
                return f"LLM error: {e}"
        return f"[LLM disabled] {prompt}"
''')

    # database/service.py
    _write_file(project_root / "database" / "service.py", '''from __future__ import annotations
from typing import Any

from sqlalchemy import JSON, Column, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker


class DatabaseService:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.metadata = MetaData()
        self.results = Table("agent_results", self.metadata,
            Column("job_id", String, primary_key=True),
            Column("data", JSON),
        )
        self.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_result(self, job_id: str, data: dict[str, Any]):
        with self.engine.begin() as conn:
            conn.execute(self.results.insert().values(job_id=job_id, data=data))

    def query_results(self) -> list[dict[str, Any]]:
        with self.engine.connect() as conn:
            rows = conn.execute(self.results.select()).fetchall()
        return [dict(r._mapping) for r in rows]
''')

    # observability/__init__.py
    _write_file(project_root / "observability" / "__init__.py", "")

    # observability/tracer.py
    _write_file(project_root / "observability" / "tracer.py", '''from __future__ import annotations
from functools import wraps

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


def init_tracer(service_name: str = "evenage-agent", endpoint: str = "http://localhost:4318/v1/traces"):
    provider = TracerProvider()
    exporter = OTLPSpanExporter(endpoint=endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)


def trace_span(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer("evenage")
            with tracer.start_as_current_span(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
''')

    # observability/metrics.py
    _write_file(project_root / "observability" / "metrics.py", '''from __future__ import annotations
from prometheus_client import Counter, Gauge, start_http_server


requests_total = Counter("evenage_requests_total", "Total agent requests")
queue_depth_gauge = Gauge("evenage_queue_depth", "Current queue depth")


def init_metrics(port: int = 8001):
    start_http_server(port)
''')


def _generate_api(project_root: Path):
    """Generate FastAPI app that uses local core/database/observability modules."""
    _write_file(project_root / "api" / "__init__.py", "")
    _write_file(project_root / "api" / "main.py", '''from __future__ import annotations
from fastapi import FastAPI

from core.message_bus import MessageBus
from database.service import DatabaseService
from observability.tracer import init_tracer
from observability.metrics import init_metrics


app = FastAPI()

bus = MessageBus("redis://redis:6379")
db = DatabaseService("postgresql://postgres:postgres@postgres:5432/evenage")

init_tracer("evenage-api", "http://jaeger:4318/v1/traces")
init_metrics(port=8001)


@app.get("/api/agents")
def list_agents():
    return {"agents": ["researcher"]}


@app.get("/api/results")
def get_results():
    return db.query_results()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''')


def _generate_agent(project_root: Path, agent_name: str):
    """Generate a default agent implementation with tools and a worker runner."""
    # agents/__init__.py (make agents a package)
    _write_file(project_root / "agents" / "__init__.py", "")
    
    # agents/<agent>/__init__.py
    _write_file(project_root / "agents" / agent_name / "__init__.py", "")
    
    # agents/<agent>/tools/__init__.py
    _write_file(project_root / "agents" / agent_name / "tools" / "__init__.py", "")
    
    # agents/<agent>/handler.py
    handler_code = f'''from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from core.agent import BaseAgent
from core.message_bus import MessageBus
from database.service import DatabaseService
from observability.tracer import trace_span
from core.llm import SimpleLLM


@dataclass
class AgentConfig:
    name: str
    redis_url: str
    database_url: str


def load_tools() -> dict[str, Any]:
    from .tools import web_search as web_search_module
    return {{
        "web_search": web_search_module.run,
    }}


class {agent_name.capitalize()}Agent(BaseAgent):
    """An example agent that performs research and summarization."""

    def __init__(self, config: AgentConfig):
        llm = SimpleLLM()
        tools = load_tools()
        super().__init__(config, llm, tools)
        self.message_bus = MessageBus(config.redis_url)
        self.db = DatabaseService(config.database_url)

    @trace_span("agent_handle_task")
    def handle(self, task: dict):
        """Handle a research task and store result."""
        job_id = str(task.get("job_id", "unknown"))
        payload = task.get("payload", {{}})
        topic = payload.get("description", "")
        search_results = self.run_tool("web_search", {{"query": topic}})
        summary = self.llm.chat("Summarize: " + str(search_results))
        self.db.save_result(job_id, {{"topic": topic, "summary": summary}})
        self.message_bus.publish("results_channel", {{"job_id": job_id, "summary": summary}})
        return {{"summary": summary}}
'''
    _write_file(project_root / "agents" / agent_name / "handler.py", handler_code)

    # agents/<agent>/tools/web_search.py
    _write_file(
        project_root / "agents" / agent_name / "tools" / "web_search.py",
        """from __future__ import annotations
from typing import Any
import os
import json


def run(params: dict[str, Any] | None = None) -> str:
    params = params or {}
    query = params.get("query", "")
    max_results = int(params.get("max_results", 5))
    api_key = os.getenv("SERPER_API_KEY")

    if not api_key:
        return (
            "Error: SERPER_API_KEY not set. "
            "Get your API key from https://serper.dev and add it to .env"
        )

    try:
        import requests

        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": max_results})
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = []
        for idx, item in enumerate(data.get("organic", [])[:max_results], 1):
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            results.append(f"{idx}. {title}\\n   {snippet}\\n   {link}")

        return "\\n\\n".join(results) if results else f"No results found for query: {query}"

    except ImportError:
        return "Error: requests library not installed. Run: pip install requests"
    except Exception as e:
        return f"Error searching web: {str(e)}"
""",
    )

    # workers/<agent>_worker.py
    _write_file(
        project_root / "workers" / f"{agent_name}_worker.py",
        f"""from __future__ import annotations
import os
import sys
import time

# Add project root to sys.path to allow imports from agents/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.{agent_name}.handler import {agent_name.capitalize()}Agent, AgentConfig


def main():
    agent_name = "{agent_name}"
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/evenage")
    cfg = AgentConfig(name=agent_name, redis_url=redis_url, database_url=database_url)
    agent = {agent_name.capitalize()}Agent(cfg)
    agent.listen()
    # Idle loop to keep container alive while listening on Redis pubsub
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
""",
    )


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

        # Generate transparent core and API
        progress.update(task, description="Generating core and API code...")
        _generate_transparent_core(project_path)
        _generate_api(project_path)

        # Seed default agent with tools and worker
        progress.update(task, description="Seeding default agent and tool...")
        _cwd = os.getcwd()
        try:
            os.chdir(project_path)
            _create_agent_files("researcher", non_interactive=True)
            _create_tool_file("web_search", non_interactive=True)
            # Create worker runner file and agent handler/tool code
            _generate_agent(project_path, "researcher")
            _create_skeleton_pipeline()
        finally:
            os.chdir(_cwd)

        # Seed readable runtime sources for transparency
        progress.update(task, description="Adding transparent runtime sources...")
        _seed_runtime_sources(project_path)

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
    """Run the EvenAge development environment (legacy alias)."""
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


@cli.group("run")
def run_group():
    """Run environment and jobs."""
    pass


@run_group.command("dev")
def run_group_dev():
    """Run the EvenAge development environment."""
    # Delegate to legacy implementation
    run_dev()


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
                "command": "python -m api.main",
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

CMD ["python", "-m", "api.main"]
"""

    with open(project_path / "Dockerfile", "w") as f:
        f.write(dockerfile_content)

    # Create requirements.txt (add Gemini and requests for web_search tool)
    requirements = """fastapi>=0.112.0
uvicorn[standard]>=0.30.0
redis>=5.0.0
pyyaml>=6.0.0
requests>=2.31.0
google-generativeai>=0.3.0
SQLAlchemy>=2.0.0
pgvector>=0.2.5
psycopg2-binary>=2.9.9
prometheus-client>=0.20.0
opentelemetry-sdk>=1.26.0
opentelemetry-exporter-otlp>=1.26.0
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

## Project Structure (transparent runtime)

```
{project_name}/
├── evenage.yml
├── docker-compose.yml
├── .env
├── api/
│   └── main.py          # FastAPI server using local modules
├── core/
│   ├── agent.py         # BaseAgent (visible and editable)
│   ├── message_bus.py   # Redis pub/sub bus
│   ├── llm.py           # Minimal local LLM wrapper
│   └── __init__.py
├── database/
│   └── service.py       # SQLAlchemy service with pgvector
├── observability/
│   ├── tracer.py        # OpenTelemetry init + decorator
│   └── metrics.py       # Prometheus metrics helpers
├── agents/
│   └── researcher/
│       ├── agent.yml
│       ├── handler.py
│       └── tools/
│           └── web_search.py
├── workers/
│   └── researcher_worker.py
└── pipelines/
    └── research_pipeline.yml
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
        "command": f"python workers/{agent_name}_worker.py",
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
