"""Runtime service that assembles core dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from swecli.core.factories import AgentFactory, AgentSuite, ToolDependencies, ToolFactory
from swecli.core.interfaces import ConfigManagerInterface, ToolRegistryInterface
from swecli.core.management import ModeManager


@dataclass
class RuntimeSuite:
    """Aggregates runtime objects used by REPL and CLI layers."""

    tool_registry: ToolRegistryInterface
    agents: AgentSuite
    agent_factory: AgentFactory
    tool_factory: ToolFactory

    def refresh_agents(self) -> None:
        """Refresh tool schemas/prompts for both agents after tool updates."""
        self.agent_factory.refresh_tools(self.agents)


class RuntimeService:
    """Builds the tool registry and agents from high-level dependencies."""

    def __init__(
        self,
        config_manager: ConfigManagerInterface,
        mode_manager: ModeManager,
    ) -> None:
        self._config_manager = config_manager
        self._mode_manager = mode_manager

    def build_suite(
        self,
        *,
        file_ops: Union[Any, None],
        write_tool: Union[Any, None],
        edit_tool: Union[Any, None],
        bash_tool: Union[Any, None],
        web_fetch_tool: Union[Any, None],
        open_browser_tool: Union[Any, None] = None,
        vlm_tool: Union[Any, None] = None,
        web_screenshot_tool: Union[Any, None] = None,
        mcp_manager: Union[Any, None] = None,
    ) -> RuntimeSuite:
        """Create a runtime suite containing the tool registry and agents."""
        tool_factory = ToolFactory(
            ToolDependencies(
                file_ops=file_ops,
                write_tool=write_tool,
                edit_tool=edit_tool,
                bash_tool=bash_tool,
                web_fetch_tool=web_fetch_tool,
                open_browser_tool=open_browser_tool,
                vlm_tool=vlm_tool,
                web_screenshot_tool=web_screenshot_tool,
            )
        )
        tool_registry = tool_factory.create_registry(mcp_manager=mcp_manager)

        agent_factory = AgentFactory(
            self._config_manager.get_config(),
            tool_registry,
            self._mode_manager,
        )
        agents = agent_factory.create_agents()

        return RuntimeSuite(
            tool_registry=tool_registry,
            agents=agents,
            agent_factory=agent_factory,
            tool_factory=tool_factory,
        )

    def rebuild_tool_registry(
        self,
        suite: RuntimeSuite,
        *,
        mcp_manager: Union[Any, None],
    ) -> ToolRegistryInterface:
        """Rebuild the tool registry when MCP connectivity changes."""
        registry = suite.tool_factory.create_registry(mcp_manager=mcp_manager)
        suite.tool_registry = registry
        suite.agent_factory = AgentFactory(
            self._config_manager.get_config(),
            registry,
            self._mode_manager,
        )
        suite.agents = suite.agent_factory.create_agents()
        return registry
