"""Core implementation of zero-configuration Nexus.

This module provides the main Nexus class for workflow orchestration
that implements true zero-configuration workflow orchestration.
"""

import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

from kailash.servers.gateway import create_gateway
from kailash.workflow import Workflow
from kailash.workflow.builder import WorkflowBuilder

# Import from SDK - remove path manipulation since we're a separate package


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NexusConfig:
    """Configuration object for Nexus components."""

    def __init__(self):
        self.strategy = None
        self.interval = 30
        self.cors_enabled = True
        self.docs_enabled = True


class Nexus:
    """Zero-configuration workflow orchestration platform.

    Like FastAPI, provides a clear instance with optional enterprise features
    configurable at construction time or via attributes.
    """

    def __init__(
        self,
        api_port: int = 8000,
        mcp_port: int = 3001,
        enable_auth: bool = False,
        enable_monitoring: bool = False,
        rate_limit: Optional[int] = None,
        auto_discovery: bool = True,
        enable_http_transport: bool = False,
        enable_sse_transport: bool = False,
        enable_discovery: bool = False,
        rate_limit_config: Optional[Dict[str, Any]] = None,
        enable_durability: bool = True,  # Disable for testing to prevent caching issues
    ):
        """Initialize Nexus with optional enterprise features.

        Args:
            api_port: Port for API server (default: 8000)
            mcp_port: Port for MCP server (default: 3001)
            enable_auth: Enable authentication (default: False)
            enable_monitoring: Enable monitoring (default: False)
            rate_limit: Requests per minute limit (default: None)
            auto_discovery: Auto-discover workflows (default: True)
            enable_http_transport: Enable HTTP transport for MCP (default: False)
            enable_sse_transport: Enable SSE transport for MCP (default: False)
            enable_discovery: Enable MCP service discovery (default: False)
            rate_limit_config: Advanced rate limiting configuration (default: None)
            enable_durability: Enable durability/caching (default: True, set False for tests)
        """
        # Configuration
        self._api_port = api_port
        self._mcp_port = mcp_port
        self._auto_discovery_enabled = auto_discovery
        self._enable_auth = enable_auth
        self._enable_monitoring = enable_monitoring
        self._enable_http_transport = enable_http_transport
        self._enable_sse_transport = enable_sse_transport
        self._enable_discovery = enable_discovery
        self._enable_durability = enable_durability
        self.rate_limit_config = rate_limit_config or {}
        self.name = "nexus"  # Platform name for MCP server

        # Internal state
        self._workflows: Dict[str, Workflow] = {}
        self._gateway = None
        self._running = False

        # Configuration objects for fine-tuning
        self.auth = NexusConfig()
        self.monitoring = NexusConfig()
        self.api = NexusConfig()
        self.mcp = NexusConfig()

        # Apply enterprise options
        if enable_auth:
            self._auth_enabled = True
        if enable_monitoring:
            self._monitoring_enabled = True
        if rate_limit:
            self._rate_limit = rate_limit

        # Create gateway with configuration
        self._initialize_gateway()

        # Initialize revolutionary capabilities
        self._initialize_revolutionary_capabilities()

        # Initialize MCP server
        self._initialize_mcp_server()

        logger.info("Nexus initialized with revolutionary workflow-native architecture")

    def _initialize_gateway(self):
        """Initialize the underlying SDK enterprise gateway."""
        try:
            # Use SDK's enterprise server with all capabilities
            self._gateway = create_gateway(
                title="Kailash Nexus - Zero-Config Workflow Platform",
                server_type="enterprise",
                enable_durability=self._enable_durability,  # Configurable for testing
                enable_resource_management=True,
                enable_async_execution=True,
                enable_health_checks=True,
                cors_origins=["*"],  # Allow CORS for browser access
                max_workers=20,  # Enterprise default
            )
            logger.info("Enterprise gateway initialized successfully")

            # Enterprise gateway already provides all capabilities we need:
            # - Multi-channel support (API, CLI, MCP)
            # - Authentication and authorization
            # - Health monitoring and metrics
            # - Resource management
            # - Durability and async execution
            # - Built-in enterprise endpoints

        except Exception as e:
            logger.error(f"Failed to initialize enterprise gateway: {e}")
            raise RuntimeError(f"Nexus requires enterprise gateway: {e}")

    def _initialize_revolutionary_capabilities(self):
        """Initialize revolutionary capabilities that differentiate Nexus from traditional frameworks."""
        # Initialize essential capability components
        self._session_manager = None  # Cross-channel session sync
        self._event_stream = None  # Real-time event communication
        self._durability_manager = None  # Request-level durability
        self._execution_contexts = {}  # Workflow execution tracking

        # Performance tracking for revolutionary targets
        self._performance_metrics = {
            "workflow_registration_time": [],
            "cross_channel_sync_time": [],
            "failure_recovery_time": [],
            "session_sync_latency": [],
        }

        # Multi-channel orchestration state
        self._channel_registry = {
            "api": {"routes": {}, "status": "pending"},
            "cli": {"commands": {}, "status": "pending"},
            "mcp": {"tools": {}, "status": "pending"},
        }

        logger.info("Revolutionary capabilities initialized")

    def _initialize_mcp_server(self):
        """Initialize MCP server for AI agent integration.

        Phase 1: Replace simple server with Core SDK's production-ready MCPServer
        """
        # When HTTP transport is disabled, use simple MCP server for WebSocket-only mode
        # Core SDK's MCPServer + MCPChannel work best with HTTP transport
        if not self._enable_http_transport:
            # Use simple MCP server for WebSocket-only mode
            from nexus.mcp import MCPServer

            self._mcp_server = MCPServer(host="0.0.0.0", port=self._mcp_port)
            self._mcp_channel = None
            # Register default Nexus resources (system, docs, config, help)
            self._register_default_mcp_resources()
            logger.info(
                f"WebSocket-only MCP server initialized on port {self._mcp_port}"
            )
            return

        try:
            # Import Core SDK's comprehensive MCP implementation for HTTP+WebSocket mode
            from kailash.channels import ChannelConfig, ChannelType, MCPChannel
            from kailash.mcp_server import MCPServer
            from kailash.mcp_server.auth import APIKeyAuth

            # Create production-ready MCP server using Core SDK
            self._mcp_server = self._create_sdk_mcp_server()

            # Create MCP channel for workflow management
            self._mcp_channel = self._setup_mcp_channel()
            logger.info(
                "✅ Full MCP protocol support enabled (tools, resources, prompts)"
            )

            logger.info(f"Production MCP server initialized on port {self._mcp_port}")

        except ImportError as e:
            # Fallback to simple implementation if Core SDK not available
            logger.warning(
                f"Core SDK MCP not available ({e}), falling back to simple MCP server"
            )
            from nexus.mcp import MCPServer

            self._mcp_server = MCPServer(host="0.0.0.0", port=self._mcp_port)
            self._mcp_channel = None
            logger.info(f"Simple MCP server initialized on port {self._mcp_port}")

    def _register_default_mcp_resources(self):
        """Register default MCP resources (system, docs, config, help)."""
        import json

        # System info resource
        async def system_info_handler(uri: str):
            info = {
                "platform": "Kailash Nexus",
                "version": getattr(self, "_version", "1.0.0"),
                "workflows": list(self._workflows.keys()),
                "api_port": self._api_port,
                "mcp_port": self._mcp_port,
            }
            return {
                "content": json.dumps(info, indent=2),
                "mimeType": "application/json",
            }

        self._mcp_server._resources["system://nexus/info"] = system_info_handler

        # Workflow resource handler (detailed)
        async def workflow_detail_handler(uri: str):
            # Extract workflow name from URI (workflow://name)
            workflow_name = uri.split("://")[1] if "://" in uri else uri
            if workflow_name not in self._workflows:
                return {
                    "content": json.dumps(
                        {"error": f"Workflow not found: {workflow_name}"}
                    ),
                    "mimeType": "application/json",
                }

            workflow = self._workflows[workflow_name]
            workflow_info = {
                "name": workflow_name,
                "type": "workflow",
                "nodes": [
                    {"id": node_id, "type": str(type(node).__name__)}
                    for node_id, node in workflow.nodes.items()
                ],
                "schema": {
                    "inputs": (
                        getattr(workflow.metadata, "parameters", {})
                        if hasattr(workflow, "metadata") and workflow.metadata
                        else {}
                    ),
                    "outputs": {},
                },
            }
            return {
                "content": json.dumps(workflow_info, indent=2),
                "mimeType": "application/json",
            }

        # Register workflow:// pattern (wildcard)
        self._mcp_server._resources["workflow://*"] = workflow_detail_handler

        # Documentation resource
        async def docs_handler(uri: str):
            docs_content = """# Nexus Quick Start Guide

Welcome to Kailash Nexus! This guide will help you get started.

## Overview
Nexus is a multi-channel platform that exposes workflows via:
- REST API
- CLI commands
- MCP protocol

## Quick Start
1. Register workflows using `app.register(name, workflow)`
2. Access via API at `/workflows/{name}`
3. Access via CLI with `nexus run {name}`
4. Access via MCP protocol as tools

For more information, visit the documentation.
"""
            return {"content": docs_content, "mimeType": "text/markdown"}

        self._mcp_server._resources["docs://quickstart"] = docs_handler

        # Configuration resource
        async def config_handler(uri: str):
            config = {
                "name": "Kailash Nexus",
                "api_port": self._api_port,
                "mcp_port": self._mcp_port,
                "features": {
                    "api": True,
                    "cli": True,
                    "mcp": True,
                    "monitoring": self._enable_monitoring,
                    "auth": self._enable_auth,
                },
            }
            return {
                "content": json.dumps(config, indent=2),
                "mimeType": "application/json",
            }

        self._mcp_server._resources["config://platform"] = config_handler

        # Help resource
        async def help_handler(uri: str):
            help_content = """# Getting Started with Nexus

## Available Workflows
"""
            for workflow_name in self._workflows.keys():
                help_content += f"- **{workflow_name}**: Workflow tool\n"

            help_content += """
## Resource URIs
- `system://nexus/info` - System information
- `workflow://<name>` - Workflow definitions
- `docs://quickstart` - Quick start guide
- `config://platform` - Platform configuration
- `help://getting-started` - This help resource

## Need Help?
Check the documentation or explore available resources.
"""
            return {"content": help_content, "mimeType": "text/markdown"}

        self._mcp_server._resources["help://getting-started"] = help_handler

    def _create_mock_mcp_server(self):
        """Create a simple mock MCP server for testing."""

        class MockMCPServer:
            def __init__(self):
                self._tools = {}
                self._resources = {}
                self._prompts = {}

            def tool(self, name=None, **kwargs):
                def decorator(func):
                    tool_name = name or func.__name__
                    self._tools[tool_name] = func
                    return func

                return decorator

            def resource(self, pattern):
                def decorator(func):
                    self._resources[pattern] = func
                    return func

                return decorator

        return MockMCPServer()

    def _create_sdk_mcp_server(self):
        """Create production-ready MCP server using Core SDK.

        This replaces the simple MCP server with the Core SDK's comprehensive
        implementation that includes authentication, caching, metrics, and
        full protocol support (tools, resources, prompts).
        """
        from kailash.mcp_server import MCPServer
        from kailash.mcp_server.auth import APIKeyAuth

        # Configure authentication if enabled
        auth_provider = None
        if self._enable_auth:
            # Use API Key auth as default
            # In production, you'd load these from environment or config
            api_keys = self._get_api_keys()
            if api_keys:
                # APIKeyAuth expects a list of keys when using simple format
                auth_provider = APIKeyAuth(list(api_keys.values()))

        # Create enhanced MCP server with all enterprise features
        server = MCPServer(
            name=f"{self.name}-mcp",
            enable_cache=True,
            enable_metrics=True,
            auth_provider=auth_provider,
            enable_http_transport=self._enable_http_transport,
            enable_sse_transport=self._enable_sse_transport,
            rate_limit_config=self.rate_limit_config,
            circuit_breaker_config={"failure_threshold": 5},
            enable_discovery=self._enable_discovery,
            enable_streaming=True,
        )

        # Register default system information as a resource
        @server.resource("system://nexus/info")
        async def get_system_info() -> Dict[str, Any]:
            """Provide Nexus system information."""
            return {
                "uri": "system://nexus/info",
                "mimeType": "application/json",
                "content": json.dumps(
                    {
                        "platform": "Kailash Nexus",
                        "version": "1.0.0",
                        "workflows": list(self._workflows.keys()),
                        "capabilities": ["tools", "resources", "prompts"],
                        "transports": self._get_enabled_transports(),
                    },
                    indent=2,
                ),
            }

        return server

    def _setup_mcp_channel(self):
        """Set up MCP channel for workflow management.

        The MCPChannel automatically exposes workflows as MCP tools and
        manages the protocol implementation details.
        """
        from kailash.channels import ChannelConfig, ChannelType, MCPChannel

        # Create channel configuration
        config = ChannelConfig(
            name=f"{self.name}-mcp-channel",
            channel_type=ChannelType.MCP,
            host="0.0.0.0",
            port=self._mcp_port,
            enable_sessions=True,
            enable_auth=self._enable_auth,
            extra_config={
                "server_name": f"{self.name}-mcp",
                "description": f"MCP channel for {self.name} platform",
                "enable_resources": True,
                "enable_prompts": True,
            },
        )

        # Create MCP channel with our enhanced server
        mcp_channel = MCPChannel(config, mcp_server=self._mcp_server)

        # The channel will automatically register workflows as tools
        # when we call register() method

        return mcp_channel

    def _register_workflow_as_mcp_tool(self, name: str, workflow):
        """Register a workflow as an MCP tool dynamically.

        This is used when MCPChannel is not available (WebSocket-only mode).
        We manually register the workflow as a tool with the Core SDK's MCPServer.
        """
        from kailash.runtime import LocalRuntime

        async def workflow_tool(**params):
            """Execute workflow with given parameters."""
            runtime = LocalRuntime()
            results, run_id = runtime.execute(workflow, params)
            return {"results": results, "run_id": run_id}

        # Register as tool with the MCPServer
        # The @tool decorator syntax won't work dynamically, so we use internal registration
        if hasattr(self._mcp_server, "_tools"):
            self._mcp_server._tools[name] = workflow_tool
            logger.info(f"Workflow '{name}' registered as MCP tool (WebSocket mode)")
        else:
            logger.warning(
                f"Could not register workflow '{name}' as MCP tool - _tools attribute missing"
            )

    def _get_api_keys(self) -> Dict[str, str]:
        """Get API keys for authentication.

        In production, load from environment or secure config.
        """
        import os

        # Example: Load from environment variables
        api_keys = {}

        # Check for NEXUS_API_KEY_* environment variables
        for key, value in os.environ.items():
            if key.startswith("NEXUS_API_KEY_"):
                user_id = key.replace("NEXUS_API_KEY_", "").lower()
                api_keys[user_id] = value

        # Default test key if none provided (development only)
        if not api_keys and not os.environ.get("NEXUS_PRODUCTION"):
            api_keys["test_user"] = "test-api-key-12345"

        return api_keys

    def _get_enabled_transports(self) -> List[str]:
        """Get list of enabled MCP transports."""
        transports = ["websocket"]  # Always enabled

        if self._enable_http_transport:
            transports.append("http")

        if self._enable_sse_transport:
            transports.append("sse")

        return transports

    def register(self, name: str, workflow: Workflow):
        """Register a workflow to be available on all channels.

        Zero-config registration: Single registration → Multi-channel exposure (API, CLI, MCP)
        Leverages the enterprise gateway's built-in multi-channel support.

        Args:
            name: Workflow identifier
            workflow: Workflow instance or WorkflowBuilder
        """
        import time

        registration_start = time.time()

        # Handle WorkflowBuilder
        if hasattr(workflow, "build"):
            workflow = workflow.build()

        # Store internally for Nexus-specific features
        self._workflows[name] = workflow

        # Register with enterprise gateway - this automatically exposes on all channels
        if self._gateway:
            try:
                self._gateway.register_workflow(name, workflow)
                logger.info(f"Workflow '{name}' registered with enterprise gateway")
            except Exception as e:
                logger.error(f"Failed to register workflow '{name}': {e}")
                raise

        # Register with MCP channel for full protocol support
        if hasattr(self, "_mcp_channel") and self._mcp_channel:
            # MCPChannel automatically exposes workflow as tool
            self._mcp_channel.register_workflow(name, workflow)
            logger.info(f"Workflow '{name}' registered with enhanced MCP channel")
        elif hasattr(self, "_mcp_server") and self._mcp_server:
            # Register workflow as MCP tool when using WebSocket wrapper
            # Core SDK MCPServer uses decorators, so we register dynamically
            if hasattr(self._mcp_server, "register_workflow"):
                # Simple MCP server has register_workflow method
                self._mcp_server.register_workflow(name, workflow)
            else:
                # Core SDK MCPServer - register as tool manually
                self._register_workflow_as_mcp_tool(name, workflow)

        # Track performance metric
        registration_time = time.time() - registration_start
        self._performance_metrics["workflow_registration_time"].append(
            registration_time
        )

        # Enhanced registration logging with full endpoint URLs
        base_url = f"http://localhost:{self._api_port}"
        logger.info(
            f"✅ Workflow '{name}' registered successfully!\n"
            f"   📡 API Endpoints:\n"
            f"      • POST   {base_url}/workflows/{name}/execute\n"
            f"      • GET    {base_url}/workflows/{name}/workflow/info\n"
            f"      • GET    {base_url}/workflows/{name}/health\n"
            f"   🤖 MCP Tool: workflow_{name}\n"
            f"   💻 CLI Command: nexus execute {name}\n"
            f"   ⏱️  Registration time: {registration_time:.3f}s"
        )

    # Multi-channel registration is handled automatically by the enterprise gateway
    # No need for custom channel registry - the gateway provides this natively

    def endpoint(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        rate_limit: Optional[int] = None,
        **fastapi_kwargs,
    ):
        """Decorator to register custom REST endpoint (API-only).

        This endpoint is API-channel only (not available in CLI or MCP).
        For multi-channel access, use register() method instead.

        Args:
            path: URL path pattern (e.g., "/api/conversations/{conversation_id}")
            methods: HTTP methods (default: ["GET"])
            rate_limit: Requests per minute limit (default: 100, None=unlimited)
            **fastapi_kwargs: Additional FastAPI route parameters
                - status_code: int - HTTP status code for successful response
                - response_model: Type - Pydantic model for response validation
                - tags: List[str] - OpenAPI tags for grouping
                - summary: str - Short description for OpenAPI
                - description: str - Long description for OpenAPI

        Returns:
            Decorator function that registers the endpoint

        Example:
            >>> @app.endpoint("/api/conversations/{conversation_id}",
            ...               methods=["GET"], rate_limit=50)
            >>> async def get_conversation(conversation_id: str):
            ...     return {"id": conversation_id}

        Raises:
            RuntimeError: If gateway not initialized
            ValueError: If invalid HTTP method provided
        """
        if methods is None:
            methods = ["GET"]

        # Use global rate limit config or endpoint-specific limit
        if rate_limit is None:
            # Check if global rate limit is configured
            rate_limit = self.rate_limit_config.get("default_rate_limit", 100)

        def decorator(func):
            # Validate gateway initialized
            if self._gateway is None:
                raise RuntimeError(
                    "Gateway not initialized. Cannot register endpoints before gateway is ready."
                )

            # SECURITY: Add rate limiting wrapper
            import time
            from collections import defaultdict
            from functools import wraps
            from typing import Dict as TypingDict

            # Simple in-memory rate limiter (per client IP)
            request_counts: TypingDict[str, TypingDict[str, int]] = defaultdict(
                lambda: defaultdict(int)
            )
            rate_limit_window = 60  # 1 minute window

            @wraps(func)
            async def rate_limited_func(*args, **kwargs):
                from fastapi import HTTPException, Request

                # Extract FastAPI Request object (not Pydantic models)
                request = None

                # Check kwargs first
                if "request" in kwargs:
                    arg = kwargs["request"]
                    if isinstance(arg, Request):
                        request = arg

                # If not found in kwargs, check args
                if request is None:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break

                # Only apply rate limiting if we have a real FastAPI Request object
                if (
                    request is not None
                    and isinstance(request, Request)
                    and rate_limit > 0
                ):
                    # Get client IP
                    client_ip = request.client.host if request.client else "unknown"
                    current_minute = int(time.time() // rate_limit_window)

                    # Check rate limit
                    if request_counts[client_ip][current_minute] >= rate_limit:
                        raise HTTPException(
                            status_code=429,
                            detail=f"Rate limit exceeded. Maximum {rate_limit} requests per minute.",
                        )

                    # Increment counter
                    request_counts[client_ip][current_minute] += 1

                    # Cleanup old entries (prevent memory leak)
                    old_minutes = [
                        m
                        for m in request_counts[client_ip].keys()
                        if m < current_minute - 5
                    ]
                    for old_minute in old_minutes:
                        del request_counts[client_ip][old_minute]

                # Call original function
                return await func(*args, **kwargs)

            # Use rate-limited wrapper
            wrapped_func = rate_limited_func

            # Get FastAPI app from gateway
            fastapi_app = self._gateway.app

            # Register route for each method
            for method in methods:
                method_lower = method.lower()

                # Validate HTTP method
                valid_methods = [
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "head",
                    "options",
                ]
                if method_lower not in valid_methods:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Register route with FastAPI
                route_func = getattr(fastapi_app, method_lower)
                route_func(path, **fastapi_kwargs)(wrapped_func)

            # Log registration
            methods_str = ", ".join(methods)
            rate_limit_str = f", rate_limit={rate_limit}/min" if rate_limit > 0 else ""
            logger.info(
                f"✅ Custom endpoint registered: {methods_str} {path} (API-only{rate_limit_str})"
            )

            return wrapped_func

        return decorator

    async def _execute_workflow(
        self, workflow_name: str, inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a registered workflow with given inputs.

        Helper method for custom endpoints to call workflows internally.
        Includes input validation and sanitization for security.

        Args:
            workflow_name: Name of registered workflow
            inputs: Input data for workflow

        Returns:
            Workflow execution results

        Raises:
            HTTPException: If workflow not found, input invalid, or execution fails
        """
        import sys

        from fastapi import HTTPException

        # Check workflow exists
        if workflow_name not in self._workflows:
            raise HTTPException(
                status_code=404, detail=f"Workflow '{workflow_name}' not found"
            )

        # SECURITY: Validate input size (prevent DoS)
        MAX_INPUT_SIZE = 10 * 1024 * 1024  # 10MB
        input_size = sys.getsizeof(inputs)
        if input_size > MAX_INPUT_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Input data too large ({input_size} bytes, max {MAX_INPUT_SIZE})",
            )

        # SECURITY: Sanitize inputs (prevent code injection)
        DANGEROUS_KEYS = [
            "__class__",
            "__builtins__",
            "__import__",
            "__globals__",
            "eval",
            "exec",
            "compile",
            "__code__",
            "__dict__",
        ]

        for key in list(inputs.keys()):
            # Check for dangerous keys
            if key in DANGEROUS_KEYS or key.startswith("__"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid input key: '{key}' (potentially dangerous)",
                )

            # Check for excessively long keys
            if len(key) > 256:
                raise HTTPException(
                    status_code=400,
                    detail=f"Input key too long: '{key[:50]}...' (max 256 chars)",
                )

        # Execute workflow via gateway
        try:
            # Get the workflow
            workflow = self._workflows[workflow_name]

            # Execute using runtime (consistent with SDK patterns)
            from kailash.runtime import get_runtime

            runtime = get_runtime("async")
            result = await runtime.execute_workflow_async(workflow, inputs)

            return result
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Workflow execution failed for '{workflow_name}': {e}")
            raise HTTPException(
                status_code=500, detail=f"Workflow execution failed: {str(e)}"
            )

    def _run_gateway(self):
        """Run gateway in thread with error handling."""
        try:
            # Gateway uses 'run' method, not 'start'
            self._gateway.run(host="0.0.0.0", port=self._api_port)
        except Exception as e:
            logger.warning(
                f"Gateway channel error: {e}. Continuing with other channels."
            )

    def _run_mcp_server(self):
        """Run MCP server in thread."""
        try:
            import asyncio

            from .mcp_websocket_server import MCPWebSocketServer

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Use MCP channel if available (full protocol support)
            if hasattr(self, "_mcp_channel") and self._mcp_channel:
                loop.run_until_complete(self._mcp_channel.start())
            else:
                # Create WebSocket server wrapper for MCP
                if hasattr(self, "_mcp_server") and self._mcp_server:
                    logger.info(
                        f"Creating WebSocket server wrapper on port {self._mcp_port}"
                    )
                    # Wrap the MCP server with WebSocket server
                    self._ws_server = MCPWebSocketServer(
                        self._mcp_server, host="0.0.0.0", port=self._mcp_port
                    )
                    # Store the task so we can clean it up later
                    self._ws_server_task = loop.create_task(self._ws_server.start())

                    # NOTE: Don't call self._mcp_server.run() here!
                    # The WebSocket wrapper handles the MCP protocol directly.
                    # Calling run() would start STDIO transport which conflicts with WebSocket.
                else:
                    # Simple server fallback
                    logger.warning("No MCP server found, skipping WebSocket setup")
                    if hasattr(self, "_mcp_server") and hasattr(
                        self._mcp_server, "start"
                    ):
                        loop.run_until_complete(self._mcp_server.start())

            loop.run_forever()
        except Exception as e:
            logger.warning(f"MCP server error: {e}. Continuing with other channels.")

    def start(self):
        """Start the Nexus platform using the enterprise gateway.

        Zero-configuration startup that leverages the SDK's enterprise server
        with built-in multi-channel support (API, CLI, MCP).

        This method blocks until the server is stopped (Ctrl+C or .stop() call).
        """
        if self._running:
            logger.warning("Nexus is already running")
            return

        if not self._gateway:
            raise RuntimeError("Enterprise gateway not initialized")

        logger.info("🚀 Starting Kailash Nexus - Zero-Config Workflow Platform")

        # Auto-discover workflows if enabled
        if self._auto_discovery_enabled:
            logger.info("🔍 Auto-discovering workflows...")
            self._auto_discover_workflows()

        # Start MCP server in background thread
        if hasattr(self, "_mcp_server"):
            self._mcp_thread = threading.Thread(
                target=self._run_mcp_server, daemon=True
            )
            self._mcp_thread.start()

        self._running = True

        # Log successful startup
        self._log_startup_success()

        # Run gateway in main thread (blocking)
        logger.info("Press Ctrl+C to stop the server")
        try:
            # Run gateway directly - this blocks until stopped
            self._gateway.run(host="0.0.0.0", port=self._api_port)
        except KeyboardInterrupt:
            logger.info("\n⏹️  Shutting down Nexus...")
            self.stop()
            logger.info("✅ Nexus stopped successfully")
        except Exception as e:
            logger.error(f"Gateway error: {e}")
            self.stop()
            raise RuntimeError(f"Nexus failed: {e}")

    def _log_startup_success(self):
        """Log successful startup with enterprise capabilities."""
        logger.info("✅ Nexus Platform Started Successfully!")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("🏗️  ENTERPRISE ARCHITECTURE ACTIVE:")
        logger.info("   📡 API Server: REST + WebSocket + OpenAPI docs")
        logger.info("   💻 CLI Interface: Interactive commands")
        logger.info("   🤖 MCP Protocol: AI agent tools")
        logger.info("   🔄 Multi-Channel: Unified workflow access")
        logger.info("")
        logger.info("📊 PLATFORM STATUS:")
        logger.info(f"   Workflows: {len(self._workflows)} registered")
        logger.info(f"   API Port: {self._api_port}")
        logger.info("   Server Type: Enterprise (production-ready)")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    def _initialize_runtime_capabilities(self):
        """Initialize runtime revolutionary capabilities.

        NOTE: This method is currently unused but reserved for v1.1 features.
        Event broadcasting uses _event_log (see broadcast_event() method).
        Session management uses lazy initialization (see create_session() method).
        """
        # TODO v1.1: Initialize session manager for cross-channel sync
        if not self._session_manager:
            from .channels import create_session_manager

            self._session_manager = create_session_manager()
            logger.info("Cross-channel session manager initialized")

        # TODO v1.1: Initialize event stream for real-time communication
        # Currently, events are logged to _event_log without real-time broadcasting
        # Real-time event streaming (WebSocket/SSE) will be added in v1.1
        if not self._event_stream:
            logger.debug(
                "Event stream initialization deferred to v1.1 (using _event_log for now)"
            )

        # TODO v1.1: Initialize durability manager for request-level persistence
        # Enterprise gateway already provides durability - this is for additional features
        if not self._durability_manager:
            logger.debug(
                "Durability manager initialization deferred to v1.1 (gateway provides base durability)"
            )

    def _activate_multi_channel_orchestration(self):
        """Activate revolutionary multi-channel orchestration."""
        total_workflows = len(self._workflows)

        logger.info(
            f"🌉 Activating multi-channel orchestration for {total_workflows} workflows..."
        )

        # Update channel status
        for channel in self._channel_registry:
            self._channel_registry[channel]["status"] = "initializing"

        logger.info("✅ Multi-channel orchestration ready")

        # Log revolutionary capabilities
        logger.info("🔥 Revolutionary capabilities active:")
        logger.info(
            "   • Durable-First Design: Every request resumable from checkpoints"
        )
        logger.info("   • Multi-Channel Native: Single workflow → API, CLI, MCP access")
        logger.info("   • Enterprise-Default: Production features enabled by default")
        logger.info("   • Cross-Channel Sync: Sessions persist across all interfaces")

    def _log_revolutionary_startup(self):
        """Log revolutionary startup success with competitive advantages."""
        logger.info("🎯 Kailash Nexus Platform Started Successfully!")
        logger.info(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        logger.info("🏗️  REVOLUTIONARY ARCHITECTURE ACTIVE:")
        logger.info("   📡 API Server: REST + WebSocket + OpenAPI docs")
        logger.info("   💻 CLI Interface: Interactive commands + auto-completion")
        logger.info("   🤖 MCP Protocol: AI agent tools + real execution")
        logger.info("   🔄 Cross-Channel: Unified sessions + real-time sync")
        logger.info("")
        logger.info("🎯 COMPETITIVE ADVANTAGES:")
        logger.info("   vs Django/FastAPI: Workflow-native vs request-response")
        logger.info("   vs Temporal: Zero infrastructure vs external engine")
        logger.info("   vs Serverless: Stateful workflows vs timeout limits")
        logger.info("   vs API Gateways: Business logic vs simple proxying")
        logger.info("")
        logger.info("📊 PLATFORM STATUS:")
        logger.info(f"   Workflows: {len(self._workflows)} registered")
        logger.info(
            f"   Channels: {len([c for c in self._channel_registry.values() if c['status'] == 'active'])} active"
        )
        logger.info("   Server Type: Enterprise (production-ready by default)")
        logger.info(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def stop(self):
        """Stop the Nexus server gracefully."""
        if not self._running:
            return

        logger.info("Stopping Nexus...")

        # Gateway cleanup is handled automatically by FastAPI's lifespan context manager
        # The lifespan shuts down the executor when uvicorn stops
        # No explicit .stop() method exists on EnterpriseWorkflowServer
        if self._gateway:
            logger.debug("Gateway shutdown handled by FastAPI lifespan")

        # Stop MCP channel/server if running
        if hasattr(self, "_mcp_channel") and self._mcp_channel:
            try:
                # MCP channel needs to be stopped in its event loop
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._mcp_channel.stop())
                loop.close()
            except Exception as e:
                logger.warning(
                    f"Error stopping MCP channel during shutdown: {type(e).__name__}: {e}"
                )
        elif hasattr(self, "_ws_server") and self._ws_server:
            try:
                # Stop WebSocket server
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._ws_server.stop())
                loop.close()
            except Exception as e:
                logger.warning(
                    f"Error stopping WebSocket server during shutdown: {type(e).__name__}: {e}"
                )
        elif hasattr(self, "_mcp_server"):
            try:
                # Fallback: stop simple server
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                if hasattr(self._mcp_server, "stop"):
                    loop.run_until_complete(self._mcp_server.stop())
                loop.close()
            except Exception as e:
                logger.warning(
                    f"Error stopping MCP server during shutdown: {type(e).__name__}: {e}"
                )

        self._running = False
        logger.info("Nexus stopped")

    def _auto_discover_workflows(self):
        """Auto-discover workflows in the current directory."""
        from .discovery import discover_workflows

        logger.info("Auto-discovering workflows...")
        discovered = discover_workflows()

        for name, workflow in discovered.items():
            if name not in self._workflows:
                self.register(name, workflow)
                logger.info(f"Auto-registered workflow: {name}")

    def health_check(self) -> Dict[str, Any]:
        """Get health status of the Nexus platform."""
        base_status = {
            "status": "healthy" if self._running else "stopped",
            "platform_type": "zero-config-workflow",
            "server_type": "enterprise",
            "workflows": len(self._workflows),
            "api_port": self._api_port,
            "enterprise_features": {
                "durability": True,
                "resource_management": True,
                "async_execution": True,
                "multi_channel": True,
                "health_monitoring": True,
            },
            "version": "nexus-v1.0",
        }

        # Add enterprise gateway health if available
        if self._gateway and hasattr(self._gateway, "health_check"):
            try:
                gateway_health = self._gateway.health_check()
                base_status["gateway_health"] = gateway_health
            except Exception as e:
                base_status["gateway_health"] = {"status": "error", "error": str(e)}

        return base_status

    # Progressive enhancement methods

    def enable_auth(self):
        """Enable authentication using SDK's enterprise auth capabilities."""
        if self._gateway and hasattr(self._gateway, "enable_auth"):
            try:
                self._gateway.enable_auth()
                logger.info("Authentication enabled via enterprise gateway")
            except Exception as e:
                logger.error(f"Failed to enable authentication: {e}")
        return self.use_plugin("auth")  # Fallback to plugin

    def enable_monitoring(self):
        """Enable monitoring using SDK's enterprise monitoring capabilities."""
        if self._gateway and hasattr(self._gateway, "enable_monitoring"):
            try:
                self._gateway.enable_monitoring()
                logger.info("Monitoring enabled via enterprise gateway")
            except Exception as e:
                logger.error(f"Failed to enable monitoring: {e}")
        return self.use_plugin("monitoring")  # Fallback to plugin

    def use_plugin(self, plugin_name: str):
        """Load and apply a plugin for additional features."""
        from .plugins import get_plugin_registry

        registry = get_plugin_registry()
        registry.apply(plugin_name, self)
        return self  # For chaining

    # Revolutionary Capabilities Implementation

    def create_session(self, session_id: str = None, channel: str = "api") -> str:
        """Create cross-channel synchronized session (Revolutionary Capability #3).

        Args:
            session_id: Optional session ID (auto-generated if None)
            channel: Channel creating the session

        Returns:
            Session ID for cross-channel use
        """
        import time
        import uuid

        if not session_id:
            session_id = str(uuid.uuid4())

        sync_start = time.time()

        # Initialize session manager if needed
        if not self._session_manager:
            from .channels import create_session_manager

            self._session_manager = create_session_manager()

        # Create session with cross-channel capability
        session = self._session_manager.create_session(session_id, channel)

        # Track sync performance (target: <50ms)
        sync_time = time.time() - sync_start
        self._performance_metrics["session_sync_latency"].append(sync_time)

        logger.info(
            f"Cross-channel session created: {session_id} by {channel} ({sync_time:.3f}s)"
        )
        return session_id

    def sync_session(self, session_id: str, channel: str) -> dict:
        """Sync session across channels (Revolutionary Capability #3).

        Args:
            session_id: Session to sync
            channel: Channel requesting sync

        Returns:
            Session data accessible across all channels
        """
        import time

        sync_start = time.time()

        if not self._session_manager:
            return {"error": "Session manager not initialized"}

        session_data = self._session_manager.sync_session(session_id, channel)

        # Track sync performance (target: <50ms)
        sync_time = time.time() - sync_start
        self._performance_metrics["cross_channel_sync_time"].append(sync_time)

        if session_data:
            logger.info(
                f"Session synced: {session_id} for {channel} ({sync_time:.3f}s)"
            )
            return session_data
        else:
            logger.warning(f"Session sync failed: {session_id} for {channel}")
            return {"error": "Session not found"}

    def broadcast_event(self, event_type: str, data: dict, session_id: str = None):
        """Log events for future broadcasting (v1.1 feature).

        NOTE: This method currently creates and logs events but does NOT broadcast
        them in real-time. Real-time event broadcasting will be added in v1.1 when
        WebSocket/SSE infrastructure is implemented.

        Args:
            event_type: Type of event (WORKFLOW_STARTED, COMPLETED, etc.)
            data: Event data
            session_id: Optional session to associate event with

        Returns:
            Event object (logged but not broadcast in v1.0)

        Planned for v1.1:
            - WebSocket broadcasting to connected clients
            - SSE (Server-Sent Events) streaming for browser clients
            - MCP notifications for AI agents
            - Cross-channel event synchronization

        Example:
            >>> event = app.broadcast_event("WORKFLOW_STARTED", {
            ...     "workflow": "data_pipeline",
            ...     "execution_id": "run_123"
            ... })
            >>> # In v1.0: Event is logged only
            >>> # In v1.1: Event will be broadcast to WebSocket/SSE clients
        """
        from datetime import datetime

        event = {
            "id": f"evt_{int(datetime.now().timestamp() * 1000)}",
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "session_id": session_id,
        }

        # Store event for future retrieval (v1.0 behavior)
        if not hasattr(self, "_event_log"):
            self._event_log = []
        self._event_log.append(event)

        # Log at debug level (not info - this isn't a real broadcast)
        logger.debug(
            f"Event logged (broadcast in v1.1): {event_type} (id: {event['id']})"
        )

        return event

    def get_events(
        self, session_id: str = None, event_type: str = None, limit: int = None
    ) -> List[dict]:
        """Retrieve logged events (helper for v1.0).

        Args:
            session_id: Filter by session ID
            event_type: Filter by event type
            limit: Maximum number of events to return (most recent first)

        Returns:
            List of matching events

        Example:
            >>> # Get all events
            >>> events = app.get_events()

            >>> # Get events for specific session
            >>> session_events = app.get_events(session_id="session_123")

            >>> # Get specific event type
            >>> workflow_events = app.get_events(event_type="WORKFLOW_COMPLETED")

            >>> # Get last 10 events
            >>> recent_events = app.get_events(limit=10)
        """
        if not hasattr(self, "_event_log"):
            return []

        events = self._event_log

        # Filter by session ID
        if session_id:
            events = [e for e in events if e.get("session_id") == session_id]

        # Filter by event type
        if event_type:
            events = [e for e in events if e.get("type") == event_type]

        # Apply limit (most recent first)
        if limit:
            events = list(reversed(events))[:limit]
            events = list(reversed(events))  # Restore chronological order

        return events

    def get_performance_metrics(self) -> dict:
        """Get revolutionary performance metrics for validation.

        Returns:
            Performance metrics showing competitive advantages
        """
        metrics = {}

        for metric_name, values in self._performance_metrics.items():
            if values:
                metrics[metric_name] = {
                    "average": sum(values) / len(values),
                    "latest": values[-1],
                    "count": len(values),
                    "target_met": self._check_performance_target(
                        metric_name, values[-1]
                    ),
                }
            else:
                metrics[metric_name] = {
                    "average": 0,
                    "latest": 0,
                    "count": 0,
                    "target_met": True,
                }

        return metrics

    def _check_performance_target(self, metric_name: str, value: float) -> bool:
        """Check if performance value meets revolutionary targets."""
        targets = {
            "workflow_registration_time": 1.0,  # <1 second
            "cross_channel_sync_time": 0.05,  # <50ms
            "failure_recovery_time": 5.0,  # <5 seconds
            "session_sync_latency": 0.05,  # <50ms
        }

        target = targets.get(metric_name, float("inf"))
        return value < target

    def get_channel_status(self) -> dict:
        """Get status of all channels for revolutionary validation.

        Returns:
            Channel status showing multi-channel orchestration
        """
        status = {}

        for channel, data in self._channel_registry.items():
            status[channel] = {
                "status": data["status"],
                "registered_workflows": len(
                    data.get("routes", data.get("commands", data.get("tools", {})))
                ),
                "capability": self._get_channel_capability(channel),
            }

        return status

    def _get_channel_capability(self, channel: str) -> str:
        """Get channel-specific capability description."""
        capabilities = {
            "api": "REST endpoints + WebSocket streaming + OpenAPI docs",
            "cli": "Interactive commands + auto-completion + progress updates",
            "mcp": "AI agent tools + resource discovery + real MCP execution",
        }
        return capabilities.get(channel, "Unknown capability")


# Legacy function for backwards compatibility
def create_nexus(**kwargs) -> Nexus:
    """Legacy function - use Nexus() directly instead.

    This function is deprecated. Use:
        app = Nexus(enable_auth=True, api_port=8000)
    Instead of:
        app = create_nexus(enable_auth=True, api_port=8000)
    """
    import warnings

    warnings.warn(
        "create_nexus() is deprecated. Use Nexus() directly: app = Nexus()",
        DeprecationWarning,
        stacklevel=2,
    )
    return Nexus(**kwargs)
