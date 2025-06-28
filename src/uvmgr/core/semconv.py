"""
Auto-generated semantic convention constants for uvmgr.
Generated from weaver-forge/registry/models/uvmgr.yaml

DO NOT EDIT - this file is auto-generated.
"""

# CLI Command Attributes
class CliAttributes:
    COMMAND = "cli.command"
    SUBCOMMAND = "cli.subcommand"
    ARGS = "cli.args"
    OPTIONS = "cli.options"
    EXIT_CODE = "cli.exit_code"
    INTERACTIVE = "cli.interactive"


# Package Management Attributes
class PackageAttributes:
    MANAGER = "package.manager"
    NAME = "package.name"
    VERSION = "package.version"
    OPERATION = "package.operation"
    DEV_DEPENDENCY = "package.dev_dependency"
    EXTRAS = "package.extras"
    SOURCE = "package.source"


# Package Operations
class PackageOperations:
    ADD = "add"
    REMOVE = "remove"
    UPDATE = "update"
    LOCK = "lock"
    SYNC = "sync"
    LIST = "list"


# Build Attributes
class BuildAttributes:
    TYPE = "build.type"
    SIZE = "build.size"
    DURATION = "build.duration"
    OUTPUT_PATH = "build.output_path"
    PYTHON_VERSION = "build.python_version"


# Build Types
class BuildTypes:
    WHEEL = "wheel"
    SDIST = "sdist"
    EXE = "exe"
    SPEC = "spec"


# Build Operations
class BuildOperations:
    BUILD = "build"
    DIST = "dist"
    WHEEL = "wheel"
    SDIST = "sdist"
    EXE = "exe"
    SPEC = "spec"


# Test Attributes
class TestAttributes:
    FRAMEWORK = "test.framework"
    OPERATION = "test.operation"
    TEST_COUNT = "test.test_count"
    PASSED = "test.passed"
    FAILED = "test.failed"
    SKIPPED = "test.skipped"
    DURATION = "test.duration"
    COVERAGE_PERCENTAGE = "test.coverage_percentage"


# Test Operations
class TestOperations:
    RUN = "run"
    COVERAGE = "coverage"
    WATCH = "watch"


# AI Attributes  
class AIAttributes:
    MODEL = "ai.model"
    PROVIDER = "ai.provider"
    OPERATION = "ai.operation"
    TOKENS_INPUT = "ai.tokens_input"
    TOKENS_OUTPUT = "ai.tokens_output"
    COST = "ai.cost"


# AI Operations
class AIOperations:
    ASSIST = "assist"
    GENERATE = "generate"
    FIX = "fix"
    PLAN = "plan"


# MCP Attributes
class McpAttributes:
    OPERATION = "mcp.operation"
    TOOL_NAME = "mcp.tool_name"
    SERVER_PORT = "mcp.server_port"


# MCP Operations
class McpOperations:
    START = "start"
    STOP = "stop"
    TOOL_CALL = "tool_call"


# Process Attributes
class ProcessAttributes:
    COMMAND = "process.command"
    EXECUTABLE = "process.executable"
    EXIT_CODE = "process.exit_code"
    DURATION = "process.duration"
    WORKING_DIRECTORY = "process.working_directory"


# Workflow Attributes
class WorkflowAttributes:
    OPERATION = "workflow.operation"
    TYPE = "workflow.type"
    DEFINITION_PATH = "workflow.definition_path"
    DEFINITION_NAME = "workflow.definition_name"
    ENGINE = "workflow.engine"
    INSTANCE_ID = "workflow.instance_id"


# Workflow Operations
class WorkflowOperations:
    RUN = "run"
    START = "start"
    STOP = "stop"
    VALIDATE = "validate"


# Cache Attributes
class CacheAttributes:
    OPERATION = "cache.operation"
    HIT = "cache.hit"
    KEY = "cache.key"
    SIZE = "cache.size"
    TTL = "cache.ttl"


# Cache Operations
class CacheOperations:
    GET = "get"
    SET = "set"
    DELETE = "delete"
    CLEAR = "clear"
    LIST = "list"


# Project Attributes
class ProjectAttributes:
    OPERATION = "project.operation"
    NAME = "project.name"
    TYPE = "project.type"
    VERSION = "project.version"
    LANGUAGE = "project.language"


# Project Operations
class ProjectOperations:
    CREATE = "create"
    INIT = "init"
    STATUS = "status"
    INFO = "info"


# Shell Attributes
class ShellAttributes:
    OPERATION = "shell.operation"
    COMMAND = "shell.command"
    INTERACTIVE = "shell.interactive"
    ENVIRONMENT = "shell.environment"


# Shell Operations
class ShellOperations:
    RUN = "run"
    EXEC = "exec"
    INTERACTIVE = "interactive"


# Server Attributes
class ServerAttributes:
    OPERATION = "server.operation"
    PORT = "server.port"
    HOST = "server.host"
    PROTOCOL = "server.protocol"
    SERVICE = "server.service"


# Server Operations
class ServerOperations:
    START = "start"
    STOP = "stop"
    STATUS = "status"
    RESTART = "restart"


# Remote Attributes
class RemoteAttributes:
    OPERATION = "remote.operation"
    URL = "remote.url"
    PROTOCOL = "remote.protocol"
    METHOD = "remote.method"


# Remote Operations
class RemoteOperations:
    FETCH = "fetch"
    PUSH = "push"
    SYNC = "sync"
    CONNECT = "connect"


# Tool Attributes
class ToolAttributes:
    OPERATION = "tool.operation"
    NAME = "tool.name"
    VERSION = "tool.version"
    TYPE = "tool.type"


# Tool Operations
class ToolOperations:
    INSTALL = "install"
    REMOVE = "remove"
    UPDATE = "update"
    LIST = "list"
    VERSION = "version"


# Index Attributes
class IndexAttributes:
    OPERATION = "index.operation"
    TYPE = "index.type"
    SIZE = "index.size"
    ENTRIES = "index.entries"


# Index Operations
class IndexOperations:
    BUILD = "build"
    UPDATE = "update"
    SEARCH = "search"
    CLEAR = "clear"


# Release Attributes
class ReleaseAttributes:
    OPERATION = "release.operation"
    VERSION = "release.version"
    TYPE = "release.type"
    TAG = "release.tag"


# Release Operations
class ReleaseOperations:
    CREATE = "create"
    PUBLISH = "publish"
    TAG = "tag"
    BUMP = "bump"


# CI Attributes
class CIAttributes:
    OPERATION = "ci.operation"
    RUNNER = "ci.runner"
    ENVIRONMENT = "ci.environment"
    TEST_COUNT = "ci.test_count"
    PASSED = "ci.passed"
    FAILED = "ci.failed"
    DURATION = "ci.duration"
    SUCCESS_RATE = "ci.success_rate"


# CI Operations
class CIOperations:
    VERIFY = "verify"
    QUICK_TEST = "quick_test"
    RUN = "run"
    SETUP = "setup"
    CLEANUP = "cleanup"
