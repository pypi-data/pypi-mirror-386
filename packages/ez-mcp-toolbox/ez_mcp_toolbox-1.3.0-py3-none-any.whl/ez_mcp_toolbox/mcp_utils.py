#!/usr/bin/env python3
"""
Shared MCP utilities for both chatbot and evaluator.
"""

import json
import os
import subprocess
import uuid
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console
from opik import track


@dataclass
class ServerConfig:
    """Configuration for an MCP server."""

    name: str
    description: str
    command: str
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None


class MCPManager:
    """Shared MCP server management functionality."""

    def __init__(self, console: Optional[Console] = None, debug: bool = False):
        self.console = console or Console()
        self.debug = debug
        self.sessions: Dict[str, ClientSession] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.exit_stack = AsyncExitStack()
        self.thread_id = str(uuid.uuid4())
        # Event loop used to create MCP sessions; used for thread-safe submissions
        self.loop: Optional[Any] = None
        # Store server configs to allow isolated per-call clients
        self._server_configs: Dict[str, ServerConfig] = {}

    def load_mcp_config(
        self, config_path: str = "ez-config.json"
    ) -> List[ServerConfig]:
        """Load MCP server configuration from JSON file."""
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
        else:
            # Use default configuration when no config file exists
            config = {
                "mcp_servers": [
                    {
                        "name": "ez-mcp-server",
                        "description": "Ez MCP server with default tools",
                        "command": "ez-mcp-server",
                        "args": [],
                    }
                ],
            }

        servers = []
        for server_data in config.get("mcp_servers", []):
            # Expand environment variables in env dict
            env = server_data.get("env", {})
            expanded_env = {}
            for key, value in env.items():
                if (
                    isinstance(value, str)
                    and value.startswith("${")
                    and value.endswith("}")
                ):
                    env_var = value[2:-1]
                    expanded_env[key] = os.getenv(env_var, "")
                else:
                    expanded_env[key] = value

            servers.append(
                ServerConfig(
                    name=server_data["name"],
                    description=server_data.get("description", ""),
                    command=server_data["command"],
                    args=server_data.get("args", []),
                    env=expanded_env if expanded_env else None,
                )
            )

        return servers

    async def connect_all_servers(self, servers: List[ServerConfig]) -> None:
        """Connect to all configured MCP servers via subprocess."""
        if not servers:
            return

        # Record the event loop this manager operates on
        try:
            import asyncio

            self.loop = asyncio.get_running_loop()
        except Exception:
            self.loop = None

        for server_config in servers:
            try:
                # Save config for isolated calls if needed
                self._server_configs[server_config.name] = server_config
                await self._connect_server(server_config)
                self.console.print(
                    f"[green]✓[/green] Connected to [bold]{server_config.name}[/bold]: {server_config.description}"
                )
            except Exception as e:
                self.console.print(
                    f"[red]✗[/red] Failed to connect to [bold]{server_config.name}[/bold]: {e}"
                )

    async def _connect_server(self, server_config: ServerConfig) -> None:
        """Connect to a single MCP server via subprocess."""
        # Set up environment variables for the subprocess
        if server_config.env:
            # Update the current process environment for the subprocess
            original_env = {}
            for key, value in server_config.env.items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = value

        try:
            # Create MCP client session using stdio client
            params = StdioServerParameters(
                command=server_config.command,
                args=server_config.args or [],
            )

            transport = await self.exit_stack.enter_async_context(stdio_client(params))
            stdin, write = transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdin, write)
            )
            await session.initialize()

            self.sessions[server_config.name] = session
        finally:
            # Restore original environment variables
            if server_config.env:
                for key, original_value in original_env.items():
                    if original_value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = original_value

    async def _get_all_tools(self) -> List[Dict[str, Any]]:
        """Aggregate tools from all connected MCP servers."""
        import asyncio

        all_tools = []
        for server_name, session in self.sessions.items():
            try:
                if self.debug:
                    self.console.print(f"🔧 Listing tools from server: {server_name}")
                tools_resp = await asyncio.wait_for(session.list_tools(), timeout=15.0)
                server_tools = _mcp_tools_to_openai_tools(tools_resp)
                # Prefix tool names with server name to avoid conflicts
                for tool in server_tools:
                    tool["function"]["name"] = (
                        f"{server_name}_{tool['function']['name']}"
                    )
                all_tools.extend(server_tools)
                if self.debug:
                    self.console.print(
                        f"✅ Retrieved {len(server_tools)} tools from {server_name}"
                    )
            except asyncio.TimeoutError:
                self.console.print(
                    f"[yellow]Warning:[/yellow] list_tools timed out for [bold]{server_name}[/bold]"
                )
            except Exception as e:
                self.console.print(
                    f"[yellow]Warning:[/yellow] Failed to get tools from [bold]{server_name}[/bold]: {e}"
                )
        return all_tools

    @track(name="execute_tool_call", type="tool")
    async def execute_tool_call(self, tool_call: Any) -> Any:
        """Execute a tool call on the appropriate MCP server."""

        fn_name = tool_call.function.name
        args_raw = tool_call.function.arguments or "{}"
        try:
            args = json.loads(args_raw)
        except json.JSONDecodeError:
            args = {}

        # Parse server name from tool name (format: server_name_tool_name)
        if "_" in fn_name:
            # Find the first underscore to split server name from tool name
            parts = fn_name.split("_", 1)
            if len(parts) == 2:
                server_name, actual_tool_name = parts
            else:
                # Fallback: treat as tool name without server prefix
                server_name = None
                actual_tool_name = fn_name
        else:
            # Fallback: try to find the tool in any server
            server_name = None
            actual_tool_name = fn_name

        if server_name and server_name in self.sessions:
            session = self.sessions[server_name]
        else:
            # Try to find the tool in any connected server
            session = None
            for srv_name, sess in self.sessions.items():
                try:
                    tools_resp = await sess.list_tools()
                    tool_names = [t.name for t in tools_resp.tools]
                    if actual_tool_name in tool_names:
                        session = sess
                        break
                except Exception:
                    continue

            if session is None:
                return f"Error: Tool '{actual_tool_name}' not found in any connected server"

        # Use isolated per-call client directly to avoid shared session issues
        if self.debug:
            print(f"🔧 Calling tool: {actual_tool_name} with args: {args}")
            self.console.print(
                f"⏳ Executing tool '{actual_tool_name}' with isolated client (6s timeout)"
            )

        try:
            isolated_result = await self._call_tool_isolated(
                server_name or next(iter(self.sessions.keys()), ""),
                actual_tool_name,
                args,
                timeout=6.0,
            )
            from .utils import process_mcp_tool_result

            processed = process_mcp_tool_result(
                isolated_result, actual_tool_name, self.debug
            )
            if self.debug:
                try:
                    preview = str(processed)
                    if len(preview) > 120:
                        preview = preview[:120] + "..."
                    self.console.print(
                        f"✅ Tool '{actual_tool_name}' returned: {preview}"
                    )
                except Exception:
                    pass
            return processed
        except Exception as e:
            if self.debug:
                print(f"❌ Tool {actual_tool_name} failed: {e}")
            return f"Error executing tool '{actual_tool_name}': {e}"

    async def _call_tool_isolated(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: float = 6.0,
    ) -> Any:
        """Call a tool using a fresh stdio MCP client to avoid loop/thread issues."""
        import asyncio

        if not server_name:
            raise RuntimeError("No MCP server available for isolated call")
        if server_name not in self._server_configs:
            raise RuntimeError(f"No server config found for '{server_name}'")
        cfg = self._server_configs[server_name]

        from mcp.client.stdio import stdio_client
        from mcp import ClientSession, StdioServerParameters

        # Set quiet mode for isolated calls to suppress server startup logs
        env = (cfg.env or {}).copy()
        env["EZ_MCP_QUIET"] = "1"

        params = StdioServerParameters(
            command=cfg.command, args=cfg.args or [], env=env
        )
        async with stdio_client(params) as (stdin, write):
            async with ClientSession(stdin, write) as session:
                await session.initialize()
                return await asyncio.wait_for(
                    session.call_tool(tool_name, arguments), timeout=timeout
                )

    # Thread-safe sync bridge to run execute_tool_call on the correct event loop
    def execute_tool_call_sync(self, tool_call: Any, timeout: float = 30.0) -> Any:
        import asyncio
        import concurrent.futures

        if self.loop is None:
            raise RuntimeError("MCPManager event loop is not initialized")
        try:
            future: concurrent.futures.Future = asyncio.run_coroutine_threadsafe(
                self.execute_tool_call(tool_call), self.loop
            )
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return f"Error executing tool '{getattr(getattr(tool_call, 'function', None), 'name', 'unknown')}': timeout"
        except Exception as e:
            return f"Error executing tool '{getattr(getattr(tool_call, 'function', None), 'name', 'unknown')}': {e}"

    def execute_tool_call_sync_safe(self, tool_call: Any, timeout: float = 6.0) -> Any:
        """Synchronous tool execution that works from any thread without event loop conflicts."""
        import asyncio
        import concurrent.futures
        import threading

        # If we're already in the correct event loop, use it
        if self.loop and threading.current_thread() == getattr(
            self.loop, "_thread", None
        ):
            try:
                return asyncio.run_coroutine_threadsafe(
                    self.execute_tool_call(tool_call), self.loop
                ).result(timeout=timeout)
            except Exception as e:
                return f"Error executing tool '{getattr(getattr(tool_call, 'function', None), 'name', 'unknown')}': {e}"

        # Otherwise, create a new event loop in a separate thread
        def run_in_new_loop() -> None:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self.execute_tool_call(tool_call))
            finally:
                new_loop.close()

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_in_new_loop)
                return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return f"Error executing tool '{getattr(getattr(tool_call, 'function', None), 'name', 'unknown')}': timeout"
        except Exception as e:
            return f"Error executing tool '{getattr(getattr(tool_call, 'function', None), 'name', 'unknown')}': {e}"

    async def close(self) -> None:
        """Close all MCP server connections."""
        await self.exit_stack.aclose()


def _mcp_tools_to_openai_tools(tools_resp: Any) -> List[Dict[str, Any]]:
    """Map MCP tool spec to OpenAI function tools."""
    tools = []
    for t in tools_resp.tools:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    # MCP provides a proper JSON schema in inputSchema
                    "parameters": t.inputSchema or {"type": "object", "properties": {}},
                },
            }
        )
    return tools
