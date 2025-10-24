"""Slash command definitions and registry."""

from typing import List, Optional


class SlashCommand:
    """Represents a slash command."""

    def __init__(self, name: str, description: str):
        """Initialize slash command.

        Args:
            name: Command name (without /)
            description: Command description
        """
        self.name = name
        self.description = description


class CommandRegistry:
    """Registry for slash commands."""

    def __init__(self):
        """Initialize command registry."""
        self._commands: List[SlashCommand] = []

    def register(self, command: SlashCommand) -> None:
        """Register a new command.

        Args:
            command: Command to register
        """
        self._commands.append(command)

    def get_commands(self) -> List[SlashCommand]:
        """Get all registered commands.

        Returns:
            List of all commands
        """
        return self._commands.copy()

    def find_matching(self, query: str) -> List[SlashCommand]:
        """Find commands matching query.

        Args:
            query: Search query

        Returns:
            List of matching commands
        """
        query_lower = query.lower()
        return [cmd for cmd in self._commands if cmd.name.startswith(query_lower)]


# Built-in slash commands registry
BUILTIN_COMMANDS = CommandRegistry()

# Session management commands
BUILTIN_COMMANDS.register(SlashCommand("help", "show available commands and help"))
BUILTIN_COMMANDS.register(SlashCommand("exit", "exit SWE-CLI"))
BUILTIN_COMMANDS.register(SlashCommand("quit", "exit SWE-CLI (alias for /exit)"))
BUILTIN_COMMANDS.register(SlashCommand("clear", "clear current session and start fresh"))
BUILTIN_COMMANDS.register(SlashCommand("history", "show command history"))
BUILTIN_COMMANDS.register(SlashCommand("sessions", "list all saved sessions"))
BUILTIN_COMMANDS.register(SlashCommand("resume", "resume a previous session"))
BUILTIN_COMMANDS.register(SlashCommand("models", "interactive model/provider selector"))
BUILTIN_COMMANDS.register(SlashCommand("mention", "insert a workspace mention"))
BUILTIN_COMMANDS.register(SlashCommand("context", "toggle context overview"))

# File operations commands
BUILTIN_COMMANDS.register(SlashCommand("tree", "show directory tree structure"))

# Execution commands
BUILTIN_COMMANDS.register(SlashCommand("run", "run a bash command"))
BUILTIN_COMMANDS.register(SlashCommand("mode", "switch between NORMAL and PLAN mode"))
BUILTIN_COMMANDS.register(SlashCommand("undo", "undo the last operation"))

# Advanced commands
BUILTIN_COMMANDS.register(SlashCommand("init", "analyze codebase and generate AGENTS.md"))
BUILTIN_COMMANDS.register(SlashCommand("mcp", "manage MCP servers and tools"))