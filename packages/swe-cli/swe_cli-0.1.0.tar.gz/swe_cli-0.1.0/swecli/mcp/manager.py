"""MCP Manager for managing MCP server connections and tool execution."""

import asyncio
import os
import sys
import threading
from pathlib import Path
from typing import Dict, List, Optional

from fastmcp import Client
from fastmcp.client.transports import (
    NpxStdioTransport,
    NodeStdioTransport,
    PythonStdioTransport,
    UvStdioTransport,
    UvxStdioTransport,
    StdioTransport,
)

from swecli.mcp.config import (
    load_config,
    save_config,
    get_project_config_path,
    merge_configs,
    prepare_server_config,
)
from swecli.mcp.models import MCPConfig, MCPServerConfig


class _SuppressStderr:
    """Context manager to temporarily suppress stderr output at the file descriptor level."""

    def __enter__(self):
        # Save the original stderr file descriptor
        self.old_stderr_fd = os.dup(2)
        # Open /dev/null
        self.devnull_fd = os.open(os.devnull, os.O_WRONLY)
        # Redirect stderr (fd 2) to /dev/null
        os.dup2(self.devnull_fd, 2)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore stderr
        os.dup2(self.old_stderr_fd, 2)
        # Close file descriptors
        os.close(self.old_stderr_fd)
        os.close(self.devnull_fd)
        return False


class MCPManager:
    """Manages MCP server connections and tool execution."""

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize MCP manager.

        Args:
            working_dir: Working directory for project-level config
        """
        self.working_dir = working_dir or Path.cwd()
        self.clients: Dict[str, Client] = {}  # server_name -> Client instance
        self.server_tools: Dict[str, List[Dict]] = {}  # server_name -> list of tool schemas
        self._config: Optional[MCPConfig] = None
        self._event_loop = None  # Shared event loop for all MCP operations
        self._loop_thread = None  # Background thread running the event loop
        self._loop_started = threading.Event()  # Signal when loop is ready

    def _create_transport(self, command: str, args: List[str], env: Optional[Dict[str, str]]):
        """Create appropriate transport based on command type.

        Args:
            command: Command to run (npx, node, python, uv, uvx, etc.)
            args: Command arguments
            env: Environment variables

        Returns:
            Transport object for fastmcp Client
        """
        # Map command types to transport classes
        if command == "npx":
            # For npx, first arg should be package name
            if args:
                package = args[0]
                remaining_args = args[1:]
                return NpxStdioTransport(package=package, args=remaining_args)
            else:
                raise ValueError("npx command requires at least one argument (package name)")

        elif command == "node":
            # For node, first arg should be script path
            if args:
                script = args[0]
                remaining_args = args[1:]
                return NodeStdioTransport(script=script, args=remaining_args)
            else:
                raise ValueError("node command requires at least one argument (script path)")

        elif command in ["python", "python3"]:
            # For python, first arg should be script path
            if args:
                script = args[0]
                remaining_args = args[1:]
                return PythonStdioTransport(script=script, args=remaining_args)
            else:
                raise ValueError("python command requires at least one argument (script path)")

        elif command == "uv":
            # For uv, need to parse subcommand
            if args:
                return UvStdioTransport(args=args)
            else:
                raise ValueError("uv command requires arguments")

        elif command == "uvx":
            # For uvx, first arg should be package name
            if args:
                package = args[0]
                remaining_args = args[1:]
                # UvxStdioTransport might not support env
                return UvxStdioTransport(package=package, args=remaining_args)
            else:
                raise ValueError("uvx command requires at least one argument (package name)")

        elif command == "docker":
            # Docker runs as a generic command with all args
            return StdioTransport(command=command, args=args, env=env)

        else:
            # Generic stdio transport for other commands - this one supports env
            return StdioTransport(command=command, args=args, env=env)

    def _run_event_loop(self):
        """Run event loop in background thread."""
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)
        self._loop_started.set()  # Signal that loop is ready
        try:
            self._event_loop.run_forever()
        finally:
            self._event_loop.close()

    def _ensure_event_loop(self):
        """Ensure background event loop is running."""
        if self._event_loop is None or not self._event_loop.is_running():
            self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self._loop_thread.start()
            self._loop_started.wait()  # Wait for loop to be ready

    def _run_coroutine_threadsafe(self, coro, timeout=30):
        """Run a coroutine in the shared event loop and wait for result.

        Args:
            coro: Coroutine to run
            timeout: Timeout in seconds

        Returns:
            Result of the coroutine
        """
        self._ensure_event_loop()
        future = asyncio.run_coroutine_threadsafe(coro, self._event_loop)
        return future.result(timeout=timeout)

    def load_configuration(self) -> MCPConfig:
        """Load MCP configuration from global and project files.

        Returns:
            Merged MCP configuration
        """
        # Load global config
        global_config = load_config()

        # Load project config if exists
        project_config_path = get_project_config_path(self.working_dir)
        project_config = load_config(project_config_path) if project_config_path else None

        # Merge configs
        self._config = merge_configs(global_config, project_config)
        return self._config

    def get_config(self) -> MCPConfig:
        """Get loaded configuration.

        Returns:
            MCP configuration
        """
        if self._config is None:
            self._config = self.load_configuration()
        return self._config

    async def connect(self, server_name: str) -> bool:
        """Connect to an MCP server.

        Args:
            server_name: Name of the server to connect to

        Returns:
            True if connection successful, False otherwise
        """
        config = self.get_config()

        if server_name not in config.mcp_servers:
            print(f"Error: Server '{server_name}' not found in configuration")
            return False

        server_config = config.mcp_servers[server_name]

        if not server_config.enabled:
            print(f"Warning: Server '{server_name}' is disabled")
            return False

        # Prepare config (expand env vars)
        prepared_config = prepare_server_config(server_config)

        try:
            # Suppress stderr during connection to hide MCP server logs
            with _SuppressStderr():
                # Create transport based on command type
                transport = self._create_transport(
                    prepared_config.command,
                    prepared_config.args,
                    prepared_config.env
                )

                # Create FastMCP client
                client = Client(transport)
                await client.__aenter__()

            # Store client (outside stderr suppression)
            self.clients[server_name] = client

            # Discover tools
            await self._discover_tools(server_name)

            return True

        except Exception as e:
            print(f"Error connecting to MCP server '{server_name}': {e}")
            return False

    async def disconnect(self, server_name: str) -> None:
        """Disconnect from an MCP server.

        Args:
            server_name: Name of the server to disconnect from
        """
        if server_name in self.clients:
            client = self.clients[server_name]
            try:
                # Suppress stderr during disconnect to hide MCP server logs
                with _SuppressStderr():
                    await client.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error disconnecting from '{server_name}': {e}")
            finally:
                del self.clients[server_name]
                if server_name in self.server_tools:
                    del self.server_tools[server_name]

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        server_names = list(self.clients.keys())
        for server_name in server_names:
            await self.disconnect(server_name)

    async def _discover_tools(self, server_name: str) -> None:
        """Discover tools from an MCP server.

        Args:
            server_name: Name of the server
        """
        if server_name not in self.clients:
            return

        client = self.clients[server_name]

        try:
            # List tools from the server
            tools = await client.list_tools()

            # Convert to our format
            tool_schemas = []
            for tool in tools:
                tool_schema = {
                    "name": f"mcp__{server_name}__{tool.name}",
                    "description": tool.description or f"Tool from {server_name} MCP server",
                    "input_schema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
                    "mcp_server": server_name,
                    "mcp_tool_name": tool.name,
                }
                tool_schemas.append(tool_schema)

            self.server_tools[server_name] = tool_schemas

        except Exception as e:
            print(f"Error discovering tools from '{server_name}': {e}")
            self.server_tools[server_name] = []

    async def connect_enabled_servers(self) -> Dict[str, bool]:
        """Connect to all enabled servers with auto_start=True.

        Returns:
            Dict mapping server names to connection success status
        """
        config = self.get_config()
        results = {}

        for server_name, server_config in config.mcp_servers.items():
            if server_config.enabled and server_config.auto_start:
                success = await self.connect(server_name)
                results[server_name] = success

        return results

    # Synchronous wrappers that use the shared event loop

    def connect_sync(self, server_name: str) -> bool:
        """Connect to an MCP server (synchronous wrapper).

        Args:
            server_name: Name of the server to connect to

        Returns:
            True if connection successful, False otherwise
        """
        return self._run_coroutine_threadsafe(self.connect(server_name))

    def disconnect_sync(self, server_name: str) -> None:
        """Disconnect from an MCP server (synchronous wrapper).

        Args:
            server_name: Name of the server to disconnect from
        """
        self._run_coroutine_threadsafe(self.disconnect(server_name))

    def disconnect_all_sync(self) -> None:
        """Disconnect from all MCP servers (synchronous wrapper)."""
        self._run_coroutine_threadsafe(self.disconnect_all())

    def connect_enabled_servers_sync(self) -> Dict[str, bool]:
        """Connect to all enabled servers (synchronous wrapper).

        Returns:
            Dict mapping server names to connection success status
        """
        return self._run_coroutine_threadsafe(self.connect_enabled_servers())

    def call_tool_sync(self, server_name: str, tool_name: str, arguments: Dict) -> Dict:
        """Execute an MCP tool (synchronous wrapper).

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool (without mcp__server__ prefix)
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        return self._run_coroutine_threadsafe(self.call_tool(server_name, tool_name, arguments))

    def get_all_tools(self) -> List[Dict]:
        """Get all tools from all connected servers.

        Returns:
            List of tool schemas
        """
        all_tools = []
        for server_name, tools in self.server_tools.items():
            all_tools.extend(tools)
        return all_tools

    def get_server_tools(self, server_name: str) -> List[Dict]:
        """Get tools from a specific server.

        Args:
            server_name: Name of the server

        Returns:
            List of tool schemas for that server
        """
        return self.server_tools.get(server_name, [])

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict) -> Dict:
        """Execute an MCP tool.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool (without mcp__server__ prefix)
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if server_name not in self.clients:
            return {
                "success": False,
                "error": f"Not connected to server '{server_name}'",
            }

        client = self.clients[server_name]

        try:
            result = await client.call_tool(tool_name, arguments)

            # Extract text content from result
            if hasattr(result, "content") and result.content:
                content = result.content[0].text if result.content else ""
            else:
                content = str(result)

            return {
                "success": True,
                "output": content,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
            }

    def add_server(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> None:
        """Add a new MCP server to configuration.

        Args:
            name: Server name
            command: Command to start the server
            args: Command arguments
            env: Environment variables
        """
        config = self.get_config()

        server_config = MCPServerConfig(
            command=command,
            args=args,
            env=env or {},
            enabled=True,
            auto_start=True,
        )

        config.mcp_servers[name] = server_config
        save_config(config)

        # Reload config
        self._config = None

    def remove_server(self, name: str) -> bool:
        """Remove an MCP server from configuration.

        Args:
            name: Server name

        Returns:
            True if server was removed, False if not found
        """
        config = self.get_config()

        if name not in config.mcp_servers:
            return False

        del config.mcp_servers[name]
        save_config(config)

        # Reload config
        self._config = None

        return True

    def enable_server(self, name: str) -> bool:
        """Enable an MCP server.

        Args:
            name: Server name

        Returns:
            True if server was enabled, False if not found
        """
        config = self.get_config()

        if name not in config.mcp_servers:
            return False

        config.mcp_servers[name].enabled = True
        save_config(config)

        # Reload config
        self._config = None

        return True

    def disable_server(self, name: str) -> bool:
        """Disable an MCP server.

        Args:
            name: Server name

        Returns:
            True if server was disabled, False if not found
        """
        config = self.get_config()

        if name not in config.mcp_servers:
            return False

        config.mcp_servers[name].enabled = False
        save_config(config)

        # Reload config
        self._config = None

        return True

    def list_servers(self) -> Dict[str, MCPServerConfig]:
        """List all configured MCP servers.

        Returns:
            Dict mapping server names to their configurations
        """
        config = self.get_config()
        return dict(config.mcp_servers)

    def is_connected(self, server_name: str) -> bool:
        """Check if a server is connected.

        Args:
            server_name: Name of the server

        Returns:
            True if connected, False otherwise
        """
        return server_name in self.clients
