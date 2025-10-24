"""Interactive REPL for SWE-CLI."""

import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from swecli.core.approval import ApprovalManager
from swecli.core.management import (
    ConfigManager,
    ModeManager,
    OperationMode,
    SessionManager,
    UndoManager,
)
from swecli.core.monitoring import ErrorHandler, TaskMonitor
from swecli.core.services import RuntimeService
from swecli.models.message import ChatMessage, Role
from swecli.models.operation import Operation, OperationType
from swecli.models.agent_deps import AgentDependencies
from swecli.tools.file_ops import FileOperations
from swecli.tools.write_tool import WriteTool
from swecli.tools.edit_tool import EditTool
from swecli.tools.bash_tool import BashTool
from swecli.ui.components.animations import Spinner, FlashingSymbol, ProgressIndicator
from swecli.ui.components.task_progress import TaskProgressDisplay
from swecli.ui.components.status_line import StatusLine
from swecli.ui.autocomplete import SwecliCompleter
from swecli.ui.formatters import OutputFormatter
from swecli.ui.components.notifications import NotificationCenter
from swecli.ui.formatters_internal.markdown_formatter import markdown_to_plain_text

# Command handlers
from swecli.repl.commands import (
    SessionCommands,
    FileCommands,
    ModeCommands,
    MCPCommands,
    HelpCommand,
    ConfigCommands,
)

# UI components
from swecli.repl.ui import (
    MessagePrinter,
    InputFrame,
    PromptBuilder,
    Toolbar,
    ContextDisplay,
)

# Query processing
from swecli.repl.query_processor import QueryProcessor


class REPL:
    """Interactive REPL for AI-powered coding assistance."""

    def __init__(self, config_manager: ConfigManager, session_manager: SessionManager):
        """Initialize REPL.

        Args:
            config_manager: Configuration manager
            session_manager: Session manager
        """
        self.config_manager = config_manager
        self.session_manager = session_manager
        self.config = config_manager.get_config()
        self.console = Console()

        # Initialize tools and managers
        self._init_tools()
        self._init_managers()
        self._init_runtime_service()

        # Initialize UI
        self._init_ui_components()
        self._init_prompt_session()

        # Initialize command handlers
        self._init_command_handlers()

        # Initialize query processor
        self._init_query_processor()

        self.running = True

    def _init_tools(self):
        """Initialize file operation and command tools."""
        from swecli.tools.web_fetch_tool import WebFetchTool
        from swecli.tools.open_browser_tool import OpenBrowserTool
        from swecli.tools.vlm_tool import VLMTool
        from swecli.tools.web_screenshot_tool import WebScreenshotTool
        from swecli.mcp.manager import MCPManager

        self.file_ops = FileOperations(self.config, self.config_manager.working_dir)
        self.write_tool = WriteTool(self.config, self.config_manager.working_dir)
        self.edit_tool = EditTool(self.config, self.config_manager.working_dir)
        self.bash_tool = BashTool(self.config, self.config_manager.working_dir)
        self.web_fetch_tool = WebFetchTool(self.config, self.config_manager.working_dir)
        self.open_browser_tool = OpenBrowserTool(self.config, self.config_manager.working_dir)
        self.vlm_tool = VLMTool(self.config, self.config_manager.working_dir)
        self.web_screenshot_tool = WebScreenshotTool(self.config, self.config_manager.working_dir)
        self.mcp_manager = MCPManager(working_dir=self.config_manager.working_dir)

    def _init_managers(self):
        """Initialize operation managers."""
        self.mode_manager = ModeManager()
        self.approval_manager = ApprovalManager(self.console)
        self.error_handler = ErrorHandler(self.console)
        self.undo_manager = UndoManager(self.config.max_undo_history)

    def _init_runtime_service(self):
        """Initialize runtime service with tool registry and agents."""
        self.runtime_service = RuntimeService(self.config_manager, self.mode_manager)
        self.runtime_suite = self.runtime_service.build_suite(
            file_ops=self.file_ops,
            write_tool=self.write_tool,
            edit_tool=self.edit_tool,
            bash_tool=self.bash_tool,
            web_fetch_tool=self.web_fetch_tool,
            open_browser_tool=self.open_browser_tool,
            vlm_tool=self.vlm_tool,
            web_screenshot_tool=self.web_screenshot_tool,
            mcp_manager=self.mcp_manager,
        )

        self.tool_registry = self.runtime_suite.tool_registry
        self.normal_agent = self.runtime_suite.agents.normal
        self.planning_agent = self.runtime_suite.agents.planning
        self.agent = self.normal_agent  # Default to normal agent

    def _init_ui_components(self):
        """Initialize UI components and state."""
        # UI Components
        self.spinner = Spinner(self.console)
        self.status_line = StatusLine(self.console)
        self.output_formatter = OutputFormatter(self.console)
        self._notification_center = NotificationCenter(self.console)

        # UI state trackers
        self._last_latency_ms: Optional[int] = None
        self._context_sidebar_visible = False
        self._last_prompt: str = ""
        self._last_operation_summary: str = "—"
        self._last_error: Optional[str] = None
        self._key_bindings = self._build_key_bindings()

        # Message printer and input frame
        self.message_printer = MessagePrinter(self.console)
        self.input_frame = InputFrame(self.console)
        self.prompt_builder = PromptBuilder()
        self.toolbar = Toolbar(self.mode_manager, self.session_manager, self.config)
        self.context_display = ContextDisplay(
            self.console,
            self.mode_manager,
            self.session_manager,
            self.config_manager,
            self._notification_center,
        )

    def _init_prompt_session(self):
        """Initialize prompt session with history and autocomplete."""
        # Setup prompt session with history
        history_file = Path(self.config.swecli_dir).expanduser() / "history.txt"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        # Create autocomplete for @ mentions and / commands
        self.completer = SwecliCompleter(working_dir=self.config_manager.working_dir)

        # Elegant autocomplete styling
        autocomplete_style = Style.from_dict({
            'completion-menu': 'bg:#000000',
            'completion-menu.completion': '#FFFFFF',
            'completion-menu.completion.current': 'bg:#2A2A2A #FFFFFF',
            'completion-menu.meta': '#808080',
            'completion-menu.completion.current.meta': '#A0A0A0',
            'mode-normal': 'bold #ff9f43',
            'mode-plan': 'bold #2ecc71',
            'toolbar-text': '#aaaaaa',
        })

        self.prompt_session: PromptSession[str] = PromptSession(
            history=FileHistory(str(history_file)),
            completer=self.completer,
            complete_while_typing=True,
            key_bindings=self._key_bindings,
            style=autocomplete_style,
            bottom_toolbar=self.toolbar.build_tokens,
        )

    def _init_command_handlers(self):
        """Initialize slash command handlers."""
        self.session_commands = SessionCommands(
            self.console,
            self.session_manager,
            self.config_manager,
        )

        self.file_commands = FileCommands(
            self.console,
            self.file_ops,
        )

        self.mode_commands = ModeCommands(
            self.console,
            self.mode_manager,
            self.undo_manager,
            self.approval_manager,
        )

        self.config_commands = ConfigCommands(
            self.console,
            self.config_manager,
            chat_app=None,  # Will be set by ReplChat
        )

        self.mcp_commands = MCPCommands(
            self.console,
            self.mcp_manager,
            refresh_runtime_callback=self._refresh_runtime_tooling,
            agent=self.agent,
        )

        self.help_command = HelpCommand(
            self.console,
            self.mode_manager,
        )

    def _init_query_processor(self):
        """Initialize query processor for AI interactions."""
        self.query_processor = QueryProcessor(
            self.console,
            self.session_manager,
            self.config,
            self.config_manager,
            self.mode_manager,
            self.file_ops,
            self.output_formatter,
            self.status_line,
            self._print_markdown_message,
        )
        self.query_processor.set_notification_center(self._notification_center)

    def _refresh_runtime_tooling(self) -> None:
        """Refresh tool registry and agent metadata after MCP changes."""
        if hasattr(self.tool_registry, "set_mcp_manager"):
            self.tool_registry.set_mcp_manager(self.mcp_manager)
        self.runtime_suite.refresh_agents()

    def _build_key_bindings(self) -> KeyBindings:
        """Configure prompt key bindings for high-speed workflows."""
        kb = KeyBindings()

        @kb.add("s-tab")
        def _(event) -> None:
            new_mode = (
                OperationMode.PLAN
                if self.mode_manager.current_mode == OperationMode.NORMAL
                else OperationMode.NORMAL
            )
            self.mode_manager.set_mode(new_mode)

            if hasattr(self, "approval_manager"):
                self.approval_manager.reset_auto_approve()

            # Switch agent based on mode
            if new_mode == OperationMode.PLAN:
                self.agent = self.planning_agent
            else:
                self.agent = self.normal_agent

            self._notify(
                f"Switched to {new_mode.value.upper()} mode.",
                level="info",
                toast=False,
            )
            event.app.invalidate()

        return kb

    def _print_markdown_message(
        self,
        content: str,
        *,
        symbol: str = "⏺",
    ) -> None:
        """Render assistant content as simple plain text with a leading symbol."""
        self.message_printer.print_markdown_message(content, symbol=symbol)

    def _notify(self, message: str, level: str = "info", *, toast: bool = True) -> None:
        """Record a notification and optionally display a toast."""
        title_map = {
            "info": ("Info", "cyan"),
            "warning": ("Warning", "yellow"),
            "error": ("Error", "red"),
        }
        title, style = title_map.get(level, ("Info", "cyan"))
        self._notification_center.add(level, message)
        if toast:
            self.console.print(Panel(message, title=title, border_style=style, expand=False))

    def _show_notifications(self) -> None:
        """Render the notification center."""
        self.console.print()
        self._notification_center.render()

    def _render_context_overview(self) -> None:
        """Render a compact context sidebar above the prompt."""
        self.context_display.render(
            last_prompt=self._last_prompt,
            last_operation_summary=self._last_operation_summary,
            last_error=self._last_error,
        )

    def start(self) -> None:
        """Start the REPL loop."""
        self._print_welcome()

        # Connect to enabled MCP servers
        self._connect_mcp_servers()

        # Load context files
        context_files = self.config_manager.load_context_files()
        if context_files:
            system_message = ChatMessage(
                role=Role.SYSTEM,
                content="\n\n".join(context_files),
            )
            self.session_manager.add_message(system_message, self.config.auto_save_interval)

        while self.running:
            try:
                if self._context_sidebar_visible:
                    self._render_context_overview()

                self.input_frame.print_top()
                user_input = self.prompt_session.prompt(self.prompt_builder.build_tokens())
                self.input_frame.print_bottom()

                if not user_input.strip():
                    continue

                # Check for slash commands
                if user_input.startswith("/"):
                    self._handle_command(user_input)
                    continue

                self._last_prompt = user_input.strip()

                # Process as regular query
                self._process_query(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Exiting...[/yellow]")
                self.running = False
                break
            except EOFError:
                break

        self._cleanup()

    def _print_welcome(self) -> None:
        """Print compact welcome banner using shared welcome module."""
        from swecli.ui.components.welcome import WelcomeMessage

        # Generate welcome content using shared module
        welcome_lines = WelcomeMessage.generate_full_welcome(
            current_mode=self.mode_manager.current_mode,
            working_dir=self.config_manager.working_dir,
        )

        # Print each line with Rich formatting
        for line in welcome_lines:
            # Apply color based on content
            if line.startswith("╔") or line.startswith("║") or line.startswith("╚"):
                self.console.print(f"[white]{line}[/white]")
            elif "Essential Commands:" in line:
                self.console.print(f"[bold white]{line}[/bold white]")
            elif "/help" in line or "/tree" in line or "/mode" in line:
                styled = line.replace("/help", "[cyan]/help[/cyan]")
                styled = styled.replace("/tree", "[cyan]/tree[/cyan]")
                styled = styled.replace("/mode plan", "[cyan]/mode plan[/cyan]")
                styled = styled.replace("/mode normal", "[cyan]/mode normal[/cyan]")
                self.console.print(styled)
            elif "Shortcuts:" in line:
                styled = f"[bold white]{line.split(':')[0]}:[/bold white]"
                rest = line.split(':', 1)[1] if ':' in line else ""
                styled += rest.replace("Shift+Tab", "[yellow]Shift+Tab[/yellow]")
                styled = styled.replace("@file", "[yellow]@file[/yellow]")
                styled = styled.replace("↑↓", "[yellow]↑↓[/yellow]")
                self.console.print(styled)
            elif "Session:" in line:
                mode = self.mode_manager.current_mode.value.upper()
                mode_color = "green" if mode == "PLAN" else "yellow"
                styled = f"[bold white]{line.split(':')[0]}:[/bold white]"
                rest = line.split(':', 1)[1] if ':' in line else ""
                if mode in rest:
                    rest = rest.replace(mode, f"[{mode_color}]{mode}[/{mode_color}]")
                styled += rest
                self.console.print(styled)
            else:
                self.console.print(line)


    def _process_query(self, query: str) -> None:
        """Process a user query with AI using ReAct pattern.

        Args:
            query: User query
        """
        # Delegate to query processor
        result = self.query_processor.process_query(
            query,
            self.agent,
            self.tool_registry,
            self.approval_manager,
            self.undo_manager,
        )

        # Update state from query processor results
        self._last_operation_summary, self._last_error, self._last_latency_ms = result

    def _handle_command(self, command: str) -> None:
        """Handle slash commands.

        Args:
            command: Command string (including /)
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Route to command handlers
        if cmd == "/help":
            self.help_command.handle(args)
        elif cmd == "/exit" or cmd == "/quit":
            self.running = False
        elif cmd == "/clear":
            self.session_commands.clear()
        elif cmd == "/sessions":
            self.session_commands.list_sessions()
        elif cmd == "/resume":
            self.session_commands.resume(args)
        elif cmd == "/context":
            self._context_sidebar_visible = not self._context_sidebar_visible
            state = "visible" if self._context_sidebar_visible else "hidden"
            self._notify(f"Context guide {state}.", level="info")
        elif cmd == "/tree":
            self.file_commands.show_tree(args)
        elif cmd == "/mode":
            result = self.mode_commands.switch_mode(args)
            # Sync agent after mode switch
            if result.success and result.data:
                new_mode = result.data
                if new_mode == OperationMode.PLAN:
                    self.agent = self.planning_agent
                else:
                    self.agent = self.normal_agent
        elif cmd == "/undo":
            self.mode_commands.undo()
        elif cmd == "/history":
            self.mode_commands.show_history()
        elif cmd == "/models":
            self.config_commands.show_model_selector()
        elif cmd == "/mcp":
            self.mcp_commands.handle(args)
        elif cmd == "/init":
            self._init_codebase(command)
        elif cmd == "/run":
            self._run_command(args)
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("Type /help for available commands.")

    def _init_codebase(self, command: str) -> None:
        """Handle /init command to analyze codebase and generate AGENTS.md.

        Args:
            command: The full command string (e.g., "/init" or "/init /path/to/project")
        """
        from swecli.commands.init_command import InitCommandHandler

        # Create handler
        handler = InitCommandHandler(self.agent, self.console)

        # Parse arguments
        try:
            args = handler.parse_args(command)
        except Exception as e:
            self.console.print(f"[red]✗ Error parsing command: {e}[/red]")
            return

        # Create dependencies
        deps = AgentDependencies(
            mode_manager=self.mode_manager,
            approval_manager=self.approval_manager,
            undo_manager=self.undo_manager,
            session_manager=self.session_manager,
            working_dir=Path.cwd(),
            console=self.console,
            config=self.config,
        )

        # Execute init command
        try:
            result = handler.execute(args, deps)

            if result["success"]:
                self.console.print(f"[green]{result['message']}[/green]")

                # Show summary of what was generated
                if "content" in result:
                    self.console.print(f"\n[dim]{result['content']}[/dim]")
            else:
                self.console.print(f"[red]{result['message']}[/red]")

        except Exception as e:
            self.console.print(f"[red]✗ Error during initialization: {e}[/red]")
            import traceback
            traceback.print_exc()

    def _run_command(self, args: str) -> None:
        """Handle /run command to execute a bash command.

        Args:
            args: Command to execute
        """
        if not args:
            self.console.print("[red]Please provide a command to run.[/red]")
            return

        command = args.strip()

        # Check if bash is enabled
        if not self.config.enable_bash:
            self.console.print("[red]Bash execution is disabled.[/red]")
            self.console.print("[dim]Enable it in config with 'enable_bash: true'[/dim]")
            return

        # Create operation
        operation = Operation(
            id=str(hash(f"{command}{datetime.now()}")),
            type=OperationType.BASH_EXECUTE,
            target=command,
            parameters={"command": command},
            created_at=datetime.now(),
        )

        # Show preview
        self.console.print(f"\n[cyan]Command to execute:[/cyan] {command}")

        # Check if approval is needed
        if not self.mode_manager.needs_approval(operation):
            operation.approved = True
        else:
            import asyncio
            result = None
            try:
                # Try to get existing event loop
                loop = asyncio.get_running_loop()
                # We're in an async context - skip approval, assume pre-approved
                operation.approved = True
            except RuntimeError:
                # No running loop - we can run synchronously
                result = asyncio.run(self.approval_manager.request_approval(
                    operation=operation,
                    preview=f"Execute: {command}"
                ))

                if not result.approved:
                    self.console.print("[yellow]Operation cancelled.[/yellow]")
                    return

        # Execute command
        try:
            bash_result = self.bash_tool.execute(command, operation=operation)

            if bash_result.success:
                self.console.print("\n[bold green]Output:[/bold green]")
                self.console.print(bash_result.stdout)
                if bash_result.stderr:
                    self.console.print("\n[bold yellow]Stderr:[/bold yellow]")
                    self.console.print(bash_result.stderr)
                self.console.print(f"\n[dim]Exit code: {bash_result.exit_code}[/dim]")
                # Record for history
                self.undo_manager.record_operation(operation)
            else:
                self.console.print(f"[red]✗ Command failed: {bash_result.error}[/red]")

        except Exception as e:
            self.error_handler.handle_error(e, operation)

    def _connect_mcp_servers(self) -> None:
        """Connect to enabled MCP servers on startup asynchronously."""
        import asyncio
        import threading

        def connect_in_background():
            """Background thread to connect to MCP servers."""
            try:
                # Get connection results using synchronous wrapper
                results = self.mcp_manager.connect_enabled_servers_sync()

                if results:
                    # Silently connect - no messages
                    self._refresh_runtime_tooling()
            except Exception:
                # Silently fail - user can check with /mcp list
                pass

        # Start connection in background thread - silently
        thread = threading.Thread(target=connect_in_background, daemon=True)
        thread.start()

    def _cleanup(self) -> None:
        """Cleanup resources."""
        # Disconnect from MCP servers
        import asyncio
        try:
            asyncio.run(self.mcp_manager.disconnect_all())
        except Exception as e:
            self.console.print(f"[yellow]Warning: Error disconnecting MCP servers: {e}[/yellow]")

        # Save current session
        if self.session_manager.current_session:
            self.session_manager.save_session()

        # No cleanup needed for Pydantic AI agent
        self.console.print("\n[cyan]Goodbye![/cyan]")
