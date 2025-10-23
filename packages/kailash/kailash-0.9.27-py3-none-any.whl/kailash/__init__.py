"""Kailash Python SDK - A framework for building workflow-based applications.

The Kailash SDK provides a comprehensive framework for creating nodes and workflows
that align with container-node architecture while allowing rapid prototyping.

New in v0.9.26: SSE Streaming Format - Converted WorkflowAPI streaming from JSON-lines to proper SSE specification
(id:, event:, data: fields with \\n\\n terminators). Events: start, complete, error, keepalive. Browser EventSource compatible.
Improved workflow_api.py SSE implementation for real-time chat and production deployment (nginx, CORS).
Previous v0.9.25: CRITICAL FIX - Multi-node workflow threading bug resolved. AsyncLocalRuntime now overrides execute()
and execute_async() methods to prevent thread creation in Docker. Fixes 100% failure rate of multi-node workflows with
connections in Docker/FastAPI deployments. All nodes now execute in proper async context with no thread creation.
Previous v0.9.24: CRITICAL FIX - Docker threading deadlock resolved. WorkflowAPI now defaults to AsyncLocalRuntime
eliminating double-threading anti-pattern in Docker/FastAPI deployments. 300x performance improvement (<100ms vs 30s timeout).
Previous v0.9.23: CRITICAL FIX - Resolved P0 variable persistence bug in PythonCodeNode and workflow parameter caching.
Fixed two-layer data leakage issue preventing variable/parameter persistence across workflow executions in Nexus deployments.
Previous v0.9.17: AsyncSQL per-pool locking eliminates lock contention bottleneck.
Achieves 100% success at 300+ concurrent operations (was 50% failure). 85% performance improvement with per-pool locks.
"""

from kailash.nodes.base import Node, NodeMetadata, NodeParameter
from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder

# Import key components for easier access
from kailash.workflow.graph import Connection, NodeInstance, Workflow
from kailash.workflow.visualization import WorkflowVisualizer

# Import middleware components (enhanced in v0.4.0)
try:
    from kailash.middleware import (
        AgentUIMiddleware,
        AIChatMiddleware,
        APIGateway,
        RealtimeMiddleware,
    )

    # Import new server classes (v0.6.7+)
    from kailash.servers import (
        DurableWorkflowServer,
        EnterpriseWorkflowServer,
        WorkflowServer,
    )

    # Import updated create_gateway function with enterprise defaults
    from kailash.servers.gateway import (
        create_basic_gateway,
        create_durable_gateway,
        create_enterprise_gateway,
        create_gateway,
    )

    _MIDDLEWARE_AVAILABLE = True
except ImportError:
    _MIDDLEWARE_AVAILABLE = False
    # Middleware dependencies not available

# For backward compatibility
WorkflowGraph = Workflow

__version__ = "0.9.27"

__all__ = [
    # Core workflow components
    "Workflow",
    "WorkflowGraph",  # Backward compatibility
    "NodeInstance",
    "Connection",
    "WorkflowBuilder",
    "WorkflowVisualizer",
    "Node",
    "NodeParameter",
    "NodeMetadata",
    "LocalRuntime",
]

# Add middleware and servers to exports if available
if _MIDDLEWARE_AVAILABLE:
    __all__.extend(
        [
            # Legacy middleware
            "AgentUIMiddleware",
            "RealtimeMiddleware",
            "APIGateway",
            "AIChatMiddleware",
            # New server classes
            "WorkflowServer",
            "DurableWorkflowServer",
            "EnterpriseWorkflowServer",
            # Gateway creation functions
            "create_gateway",
            "create_enterprise_gateway",
            "create_durable_gateway",
            "create_basic_gateway",
        ]
    )
