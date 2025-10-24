"""Agent executor for WebSocket queries with streaming support."""

from __future__ import annotations

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from swecli.web.state import WebState
from swecli.models.message import ChatMessage, Role
from swecli.models.agent_deps import AgentDependencies
from swecli.core.management import OperationMode


class AgentExecutor:
    """Executes agent queries in background with WebSocket streaming."""

    def __init__(self, state: WebState):
        """Initialize agent executor.

        Args:
            state: Shared web state
        """
        self.state = state
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def execute_query(
        self,
        message: str,
        ws_manager: Any,
    ) -> None:
        """Execute query and stream results via WebSocket.

        Args:
            message: User query
            ws_manager: WebSocket manager for broadcasting
        """
        try:
            # Broadcast message start
            await ws_manager.broadcast({
                "type": "message_start",
                "data": {"messageId": str(time.time())}
            })

            # Run agent in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._run_agent_sync,
                message,
                ws_manager,
                loop,  # Pass the event loop
            )

            # Add assistant response to session
            if response and response.get("success"):
                assistant_content = response.get("content", "")
                assistant_msg = ChatMessage(role=Role.ASSISTANT, content=assistant_content)
                self.state.add_message(assistant_msg)

            # Broadcast message complete
            await ws_manager.broadcast({
                "type": "message_complete",
                "data": {"messageId": str(time.time())}
            })

        except Exception as e:
            # Broadcast error
            await ws_manager.broadcast({
                "type": "error",
                "data": {"message": str(e)}
            })

    def _run_agent_sync(self, message: str, ws_manager: Any, loop: asyncio.AbstractEventLoop) -> Dict[str, Any]:
        """Run agent synchronously in thread pool.

        Args:
            message: User query
            ws_manager: WebSocket manager
            loop: Event loop for async operations

        Returns:
            Agent response
        """
        from swecli.core.services import RuntimeService
        from swecli.tools.file_ops import FileOperations
        from swecli.tools.write_tool import WriteTool
        from swecli.tools.edit_tool import EditTool
        from swecli.tools.bash_tool import BashTool
        from swecli.tools.web_fetch_tool import WebFetchTool
        from swecli.tools.open_browser_tool import OpenBrowserTool
        from swecli.web.web_approval_manager import WebApprovalManager
        from swecli.web.ws_tool_broadcaster import WebSocketToolBroadcaster

        # Get config and setup
        config = self.state.config_manager.get_config()
        working_dir = self.state.config_manager.working_dir

        # Initialize tools
        file_ops = FileOperations(config, working_dir)
        write_tool = WriteTool(config, working_dir)
        edit_tool = EditTool(config, working_dir)
        bash_tool = BashTool(config, working_dir)
        web_fetch_tool = WebFetchTool(config, working_dir)
        open_browser_tool = OpenBrowserTool(config, working_dir)

        # Create web-based approval manager
        web_approval_manager = WebApprovalManager(ws_manager, loop)

        # Build runtime suite
        runtime_service = RuntimeService(self.state.config_manager, self.state.mode_manager)
        runtime_suite = runtime_service.build_suite(
            file_ops=file_ops,
            write_tool=write_tool,
            edit_tool=edit_tool,
            bash_tool=bash_tool,
            web_fetch_tool=web_fetch_tool,
            open_browser_tool=open_browser_tool,
            mcp_manager=None,
        )

        # Wrap tool registry with WebSocket broadcaster
        wrapped_registry = WebSocketToolBroadcaster(
            runtime_suite.tool_registry,
            ws_manager,
            loop
        )

        # Get agent and replace its tool registry with wrapped version
        agent = runtime_suite.agents.normal
        agent.tool_registry = wrapped_registry

        # Get session messages
        session = self.state.session_manager.get_current_session()
        if not session:
            session = self.state.session_manager.create_session(
                working_directory=str(working_dir)
            )

        message_history = session.to_api_messages()

        # Create agent dependencies with web approval manager
        deps = AgentDependencies(
            mode_manager=self.state.mode_manager,
            approval_manager=web_approval_manager,  # Use web-based approval
            undo_manager=self.state.undo_manager,
            session_manager=self.state.session_manager,
            working_dir=working_dir,
            console=None,  # No console for web
            config=config,
        )

        # Run agent
        try:
            result = agent.run_sync(
                message,
                deps,
                message_history=message_history,
            )

            # Broadcast the full response as a chunk
            # (Streaming at character level will be added later)
            if result.get("success"):
                content = result.get("content", "")
                # Schedule the broadcast coroutine in the event loop
                future = asyncio.run_coroutine_threadsafe(
                    ws_manager.broadcast({
                        "type": "message_chunk",
                        "data": {"content": content}
                    }),
                    loop
                )
                # Wait for it to complete
                future.result(timeout=5)

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": f"Error: {str(e)}"
            }
