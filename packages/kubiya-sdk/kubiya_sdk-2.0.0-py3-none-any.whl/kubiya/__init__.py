"""
Kubiya SDK

A production-grade SDK for building and executing workflows on the Kubiya platform.

Quick Start:
-----------
    from kubiya import workflow, step

    # Define a workflow
    @workflow("data-pipeline", "1.0.0")
    def my_pipeline():
        return (
            step("extract", "Extract data")
            .shell("python extract.py")
            >> step("transform", "Transform data")
            .python(lambda data: process(data))
            >> step("load", "Load to database")
            .docker("postgres:latest", "psql -c 'INSERT...'")
        )

    # Execute the workflow
    from kubiya import execute_workflow
    result = execute_workflow(my_pipeline(), params={"date": "2024-01-01"})

Tool Execution:
--------------
    from kubiya.tool_templates import tool, execute_tool

    @tool(name="data_processor", requirements=["pandas"])
    def process_data(file_path: str):
        import pandas as pd
        df = pd.read_csv(file_path)
        return {"rows": len(df)}

    # Execute tool directly
    result = execute_tool("data_processor", tool_def=process_data.as_tool())
"""

from kubiya.__version__ import __version__, __author__, __email__, __license__

# Core functionality
from kubiya.core import (
    # Types
    ExecutorType,
    StepStatus,
    WorkflowStatus,
    RetryPolicy,
    ExecutionResult,
    WorkflowMetadata,
    ToolDefinition,
    ServiceSpec,
    Volume,
    # Exceptions
    KubiyaSDKError,
    WorkflowError,
    WorkflowValidationError,
    WorkflowExecutionError,
    ClientError,
    AuthenticationError,
    ToolError,
    ToolExecutionError,
)

# Enhanced execution with logging and validation
from kubiya.execution import (
    # Execution modes
    ExecutionMode,
    LogLevel,
    # Enhanced execution functions
    execute_workflow_with_logging,
    execute_workflow_logged,
    execute_workflow_events,
    execute_workflow_raw,
    # Validation
    validate_workflow_definition,
)

# DSL - Primary interface
from kubiya.dsl import (
    # Workflow creation
    workflow,
    step,
    # Executors
    python_executor,
    shell_executor,
    docker_executor,
    tool_executor,
    inline_agent_executor,
    # Control flow
    when,
    retry_policy,
    continue_on,
    # Examples
    examples,
)

# Client functionality (legacy/raw interface)
from kubiya.client import (
    KubiyaClient,
    StreamingKubiyaClient,
    execute_workflow,
)

# Tool framework
from kubiya.tool_templates import (
    # Decorators
    tool,
    shell_tool,
    docker_tool,
    # Execution
    execute_tool,
    ToolExecutor,
    # Templates
    DockerToolTemplate,
    AuthenticatedToolTemplate,
    CLIToolTemplate,
)

# Server (optional)
try:
    from kubiya.server import create_app as create_server
except ImportError:
    create_server = None

# MCP Protocol (optional)
try:
    from kubiya.mcp import KubiyaMCPServer as MCPServer
except ImportError:
    MCPServer = None

# Tools framework (optional)
try:
    from kubiya.tools import (
        Tool as ToolsModels_Tool,
        Source as ToolsModels_Source,
        Arg as ToolsModels_Arg,
        ToolOutput as ToolsModels_ToolOutput,
        tool_registry,
        FunctionTool,
        ToolManagerBridge,
        FileSpec,
        Volume as ToolsModels_Volume,
        ServiceSpec as ToolsModels_ServiceSpec,
        GitRepoSpec,
        OpenAPISpec,
        function_tool,
    )
except ImportError:
    # Tools not available
    ToolsModels_Tool = None
    ToolsModels_Source = None
    ToolsModels_Arg = None
    ToolsModels_ToolOutput = None
    tool_registry = None
    FunctionTool = None
    ToolManagerBridge = None
    FileSpec = None
    ToolsModels_Volume = None
    ToolsModels_ServiceSpec = None
    GitRepoSpec = None
    OpenAPISpec = None
    function_tool = None

# Stream functionality (optional)
try:
    from kubiya.stream import (
        NATSManager,
        nats_manager,
        IS_NATS_AVAILABLE,
    )
except ImportError:
    # Stream not available
    NATSManager = None
    nats_manager = None
    IS_NATS_AVAILABLE = False

# Sentry integration (optional)
try:
    from kubiya.core import (
        initialize_sentry,
        capture_exception,
        capture_message,
        add_breadcrumb,
        set_workflow_context,
        is_sentry_enabled,
        is_sentry_initialized,
        shutdown_sentry,
    )
except ImportError:
    # Fallback no-op functions
    initialize_sentry = lambda *args, **kwargs: False
    capture_exception = lambda *args, **kwargs: None
    capture_message = lambda *args, **kwargs: None
    add_breadcrumb = lambda *args, **kwargs: None
    set_user_context = lambda *args, **kwargs: None
    set_workflow_context = lambda *args, **kwargs: None
    is_sentry_enabled = lambda: False
    is_sentry_initialized = lambda: False
    shutdown_sentry = lambda: None


# Main exports
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    # Core types
    "ExecutorType",
    "StepStatus",
    "WorkflowStatus",
    "RetryPolicy",
    "ExecutionResult",
    "WorkflowMetadata",
    "ToolDefinition",
    "ServiceSpec",
    "Volume",
    # Exceptions
    "KubiyaSDKError",
    "WorkflowError",
    "WorkflowValidationError",
    "WorkflowExecutionError",
    "ClientError",
    "AuthenticationError",
    "ToolError",
    "ToolExecutionError",
    # Enhanced execution
    "ExecutionMode",
    "LogLevel",
    "execute_workflow_with_logging",
    "execute_workflow_logged",
    "execute_workflow_events",
    "execute_workflow_raw",
    "validate_workflow_definition",
    # DSL
    "workflow",
    "step",
    "python_executor",
    "shell_executor",
    "docker_executor",
    "tool_executor",
    "inline_agent_executor",
    "when",
    "retry_policy",
    "continue_on",
    "examples",
    # Client (legacy)
    "KubiyaClient",
    "StreamingKubiyaClient",
    "execute_workflow",
    # Tools
    "tool",
    "shell_tool",
    "docker_tool",
    "execute_tool",
    "ToolExecutor",
    "DockerToolTemplate",
    "AuthenticatedToolTemplate",
    "CLIToolTemplate",
    # Server (optional)
    "create_server",
    # MCP (optional)
    "MCPServer",
    # Tools (optional)
    "ToolsModels_Tool",
    "ToolsModels_Source",
    "ToolsModels_Arg",
    "ToolsModels_ToolOutput",
    "tool_registry",
    "FunctionTool",
    "ToolManagerBridge",
    "FileSpec",
    "ToolsModels_Volume",
    "ToolsModels_ServiceSpec",
    "GitRepoSpec",
    "OpenAPISpec",
    "function_tool",
    # Stream (optional)
    "NATSManager",
    "nats_manager",
    "IS_NATS_AVAILABLE",
    # Sentry (optional)
    "initialize_sentry",
    "capture_exception",
    "capture_message",
    "add_breadcrumb",
    "set_workflow_context",
    "is_sentry_enabled",
    "is_sentry_initialized",
    "shutdown_sentry",
]


def get_version_info() -> dict:
    """Get detailed version information."""
    return {
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "license": __license__,
        "has_server": create_server is not None,
        "has_mcp": MCPServer is not None,
        "has_tools": ToolsModels_Tool is not None,
        "has_stream": IS_NATS_AVAILABLE,
        "has_sentry": is_sentry_initialized(),
    }


# Auto-initialize Sentry if enabled via environment variables
if is_sentry_enabled():
    initialize_sentry()
    # Register shutdown handler
    import atexit
    atexit.register(shutdown_sentry)
