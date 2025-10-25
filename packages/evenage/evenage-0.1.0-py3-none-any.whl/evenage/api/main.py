"""
FastAPI server for EvenAge.

Provides REST API for job submission, status queries, and agent management.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from evenage.core.config import EvenAgeConfig, PipelineConfig, load_pipeline_config
from evenage.core.controller import Controller
from evenage.core.message_bus import MessageBus
from evenage.database.models import DatabaseService
from evenage.observability.metrics import init_metrics
from evenage.observability.tracing import init_tracing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request/Response models
class SubmitJobRequest(BaseModel):
    """Request to submit a new job."""

    pipeline_name: str
    inputs: dict[str, Any] | None = None


class JobStatusResponse(BaseModel):
    """Response for job status query."""

    job_id: str
    status: str
    pipeline: str
    tasks: dict[str, Any]
    results: dict[str, Any]


class AgentInfo(BaseModel):
    """Agent information."""

    name: str
    role: str
    goal: str
    status: str
    tools: list[str]


# Global services
config: EvenAgeConfig
message_bus: MessageBus
controller: Controller
database: DatabaseService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services."""
    global config, message_bus, controller, database

    # Load configuration
    config = EvenAgeConfig()

    # Initialize services
    message_bus = MessageBus(config.redis_url)
    controller = Controller(message_bus)
    database = DatabaseService(config.database_url)

    # Create database tables
    database.create_tables()

    # Initialize observability
    if config.enable_tracing:
        init_tracing(
            service_name="evenage-api",
            otlp_endpoint=config.otel_exporter_otlp_endpoint,
        )

    if config.enable_metrics:
        init_metrics(port=config.prometheus_metrics_port)

    logger.info("EvenAge API server started")

    yield

    logger.info("EvenAge API server shutting down")


# Create FastAPI app
app = FastAPI(
    title="EvenAge API",
    description="API for EvenAge distributed agent framework",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware - allow dashboard origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "http://dashboard:5173",  # Docker internal
        "*",  # TODO: Configure appropriately for production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "service": "EvenAge API",
        "version": "0.1.0",
        "status": "running",
        "dashboard": "http://localhost:5173",
        "docs": "/docs",
    }


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "service": "EvenAge API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    # Check Redis connection
    redis_healthy = message_bus.health_check()

    if not redis_healthy:
        raise HTTPException(status_code=503, detail="Redis connection failed")

    return {
        "status": "healthy",
        "redis": redis_healthy,
    }


@app.post("/api/jobs", response_model=dict[str, str])
async def submit_job(request: SubmitJobRequest):
    """
    Submit a new job for execution.

    Args:
        request: Job submission request

    Returns:
        Job ID
    """
    try:
        # Load pipeline configuration
        pipeline_path = f"pipelines/{request.pipeline_name}.yml"
        pipeline = load_pipeline_config(pipeline_path)

        # Submit job
        job_id = controller.submit_job(pipeline, request.inputs)

        # Create job record in database
        database.create_job(
            job_id=job_id,
            pipeline_name=request.pipeline_name,
            inputs=request.inputs,
        )

        return {"job_id": job_id, "status": "submitted"}

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a job.

    Args:
        job_id: Job identifier

    Returns:
        Job status information
    """
    job = controller.get_job_status(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        pipeline=job["pipeline"],
        tasks=job["tasks"],
        results=job["results"],
    )


@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a running job.

    Args:
        job_id: Job identifier

    Returns:
        Cancellation status
    """
    success = controller.cancel_job(job_id)

    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update database
    database.update_job_status(job_id, "cancelled")

    return {"job_id": job_id, "status": "cancelled"}


@app.get("/api/jobs", response_model=list[dict[str, Any]])
async def list_jobs():
    """List all active jobs."""
    return controller.list_active_jobs()


@app.get("/api/agents", response_model=list[AgentInfo])
async def list_agents():
    """
    List all registered agents.

    Returns:
        List of agent information
    """
    agents = message_bus.get_registered_agents()

    return [
        AgentInfo(
            name=name,
            role=metadata.get("role", ""),
            goal=metadata.get("goal", ""),
            status=metadata.get("status", "unknown"),
            tools=metadata.get("tools", []),
        )
        for name, metadata in agents.items()
    ]


@app.get("/api/agents/{agent_name}")
async def get_agent_details(agent_name: str):
    """
    Get detailed information about an agent.

    Args:
        agent_name: Agent name

    Returns:
        Agent details including recent tasks
    """
    agents = message_bus.get_registered_agents()
    
    if agent_name not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    metadata = agents[agent_name]
    queue_depth = message_bus.get_queue_depth(agent_name)
    
    return {
        "name": agent_name,
        "role": metadata.get("role", ""),
        "goal": metadata.get("goal", ""),
        "status": metadata.get("status", "unknown"),
        "tools": metadata.get("tools", []),
        "queue_depth": queue_depth,
        "last_heartbeat": metadata.get("last_heartbeat"),
    }


@app.get("/api/agents/{agent_name}/queue")
async def get_agent_queue_depth(agent_name: str):
    """
    Get the queue depth for an agent.

    Args:
        agent_name: Agent name

    Returns:
        Queue depth information
    """
    depth = message_bus.get_queue_depth(agent_name)

    return {
        "agent_name": agent_name,
        "queue_depth": depth,
    }


@app.post("/api/agents/{agent_name}/chat")
async def chat_with_agent(agent_name: str, message: dict[str, str]):
    """
    Chat with a specific agent.

    Args:
        agent_name: Agent to chat with
        message: Chat message containing 'content'

    Returns:
        Agent response
    """
    from evenage.core.message_bus import TaskMessage
    import uuid
    
    # Create a chat task
    task = TaskMessage(
        job_id=f"chat-{uuid.uuid4()}",
        source_agent="user",
        target_agent=agent_name,
        payload={
            "description": message.get("content", ""),
            "type": "chat",
        }
    )
    
    # Publish task
    message_bus.publish_task(task)
    
    return {
        "task_id": task.task_id,
        "status": "submitted",
        "message": "Chat message sent to agent",
    }


@app.get("/api/traces")
async def get_traces(limit: int = 100, agent_name: str | None = None):
    """
    Get recent traces from database.

    Args:
        limit: Maximum number of traces to return
        agent_name: Filter by agent name (optional)

    Returns:
        List of traces
    """
    # Query database for traces
    # This is a simplified version - full implementation would use SQLAlchemy
    return {
        "traces": [],
        "total": 0,
        "message": "Trace query would return results from PostgreSQL",
    }


@app.get("/api/metrics")
async def get_metrics_summary():
    """
    Get metrics summary for the dashboard.

    Returns:
        Metrics summary including task counts, token usage, etc.
    """
    agents = message_bus.get_registered_agents()
    
    return {
        "active_agents": len([a for a in agents.values() if a.get("status") == "active"]),
        "total_agents": len(agents),
        "active_jobs": len(controller.list_active_jobs()),
        "total_queue_depth": sum(
            message_bus.get_queue_depth(name) for name in agents.keys()
        ),
    }


@app.websocket("/ws/logs/{agent_name}")
async def agent_logs_websocket(websocket: WebSocket, agent_name: str):
    """
    WebSocket endpoint for streaming agent logs.

    Args:
        websocket: WebSocket connection
        agent_name: Agent to stream logs for
    """
    await websocket.accept()

    try:
        import asyncio
        
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "agent": agent_name,
            "message": f"Connected to {agent_name} logs",
        })
        
        # In production, this would tail Docker logs
        # For now, send periodic status updates
        while True:
            # Check if agent is active
            agents = message_bus.get_registered_agents()
            if agent_name in agents:
                status = agents[agent_name].get("status", "unknown")
                queue_depth = message_bus.get_queue_depth(agent_name)
                
                await websocket.send_json({
                    "type": "status",
                    "agent": agent_name,
                    "status": status,
                    "queue_depth": queue_depth,
                    "timestamp": __import__('time').time(),
                })
            
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for agent: {agent_name}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


@app.websocket("/ws/events")
async def system_events_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for system-wide events.
    
    Streams:
    - New jobs
    - Task completions
    - Agent status changes
    """
    await websocket.accept()
    
    try:
        import asyncio
        
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to system events",
        })
        
        # Stream system events
        while True:
            # In production, this would listen to Redis pub/sub
            # For now, send periodic updates
            agents = message_bus.get_registered_agents()
            jobs = controller.list_active_jobs()
            
            await websocket.send_json({
                "type": "system_status",
                "active_agents": len([a for a in agents.values() if a.get("status") == "active"]),
                "active_jobs": len(jobs),
                "timestamp": __import__('time').time(),
            })
            
            await asyncio.sleep(3)
            
    except WebSocketDisconnect:
        logger.info("System events WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


def main():
    """Run the API server."""
    import uvicorn

    config = EvenAgeConfig()

    uvicorn.run(
        "evenage.api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
