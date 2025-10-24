"""Command handlers for REPL.

This package contains all command handlers extracted from the main REPL class.
Each handler is responsible for a specific group of related commands.
"""

from swecli.repl.commands.base import CommandHandler, CommandResult
from swecli.repl.commands.session_commands import SessionCommands
from swecli.repl.commands.file_commands import FileCommands
from swecli.repl.commands.mode_commands import ModeCommands
from swecli.repl.commands.mcp_commands import MCPCommands
from swecli.repl.commands.help_command import HelpCommand
from swecli.repl.commands.config_commands import ConfigCommands

__all__ = [
    "CommandHandler",
    "CommandResult",
    "SessionCommands",
    "FileCommands",
    "ModeCommands",
    "MCPCommands",
    "HelpCommand",
    "ConfigCommands",
]
