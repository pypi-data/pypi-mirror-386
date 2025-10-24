"""Welcome banner and session info for SWE-CLI."""

from __future__ import annotations

import os
from itertools import zip_longest
from pathlib import Path
from typing import List, Optional, Tuple

from swecli.core.management import OperationMode
from swecli.ui.components.box_styles import BoxStyles


class WelcomeMessage:
    """Generate welcome banner and session information."""

    TOTAL_WIDTH = 110
    LEFT_WIDTH = 42
    RIGHT_WIDTH = TOTAL_WIDTH - 2 - LEFT_WIDTH - 1  # account for interior divider

    @staticmethod
    def get_version() -> str:
        """Get SWE-CLI version."""
        try:
            from importlib.metadata import version

            return f"v{version('swecli')}"
        except Exception:
            return "v0.3.0"  # Fallback version when metadata unavailable

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @classmethod
    def _inner_width(cls) -> int:
        return cls.TOTAL_WIDTH - 2

    @classmethod
    def _fit(cls, text: str, width: int) -> str:
        """Truncate text neatly to fit within the target width."""
        if len(text) <= width:
            return text.ljust(width)
        if width <= 1:
            return text[:width]
        return f"{text[: width - 1]}…"

    @classmethod
    def _format(cls, text: str, width: int, align: str = "left") -> str:
        """Format text with alignment while respecting width constraints.

        Handles ANSI escape codes properly by calculating visible length.
        """
        import re

        if not text:
            base = "".ljust(width)
        else:
            # Calculate visible length (without ANSI codes)
            visible_text = re.sub(r'\033\[[0-9;]+m', '', text)
            visible_len = len(visible_text)

            # Truncate if needed
            if visible_len > width:
                truncated = text if visible_len <= width else cls._fit(text, width)
                visible_len = len(re.sub(r'\033\[[0-9;]+m', '', truncated))
            else:
                truncated = text

            # Add padding based on visible length
            padding_needed = width - visible_len
            if padding_needed > 0:
                if align == "center":
                    left_pad = padding_needed // 2
                    right_pad = padding_needed - left_pad
                    base = " " * left_pad + truncated + " " * right_pad
                elif align == "right":
                    base = " " * padding_needed + truncated
                else:
                    base = truncated + " " * padding_needed
            else:
                base = truncated
        return base

    @classmethod
    def _two_column(
        cls,
        left: str,
        right: str,
        *,
        left_align: str = "left",
        right_align: str = "left",
    ) -> str:
        left_block = cls._format(left, cls.LEFT_WIDTH, align=left_align)
        right_block = cls._format(right, cls.RIGHT_WIDTH, align=right_align)
        # Use plain box characters with color - simpler is better
        border = f"{BoxStyles.BORDER_COLOR}│{BoxStyles.RESET}"
        return f"{border}{left_block}{border}{right_block}{border}"

    @classmethod
    def _header_line(cls, title: str) -> str:
        return BoxStyles.top_border(cls.TOTAL_WIDTH, title=title)

    @classmethod
    def _footer_line(cls) -> str:
        return BoxStyles.bottom_border(cls.TOTAL_WIDTH)

    @staticmethod
    def _shorten_path(path: Path, width: int) -> str:
        text = str(path.expanduser())
        if len(text) <= width:
            return text
        return f"…{text[-(width - 1):]}" if width > 1 else text[:width]

    # ------------------------------------------------------------------
    # Public generators
    # ------------------------------------------------------------------
    @classmethod
    def generate_banner(cls) -> List[str]:
        """Generate the top banner without session details."""
        version = cls.get_version()
        header = cls._header_line(f"SWE-CLI {version}")
        welcome_line = cls._two_column(
            "Welcome to your coding assistant",
            "Launch commands: /help · /mode plan · /mode normal",
            left_align="center",
        )
        footer = cls._footer_line()
        return [header, welcome_line, footer]

    @staticmethod
    def generate_commands_section() -> List[str]:
        """Provide quick command hints."""
        return [
            "Quick Commands",
            " • /help           Show available commands",
            " • /tree           Explore the project tree",
            " • /mode normal    Run with approvals",
            " • /mode plan      Plan without execution",
        ]

    @staticmethod
    def generate_shortcuts_section() -> List[str]:
        """Provide keyboard shortcut hints."""
        return [
            "Keyboard Shortcuts",
            " • Shift+Tab       Toggle plan/normal mode",
            " • @file           Mention a file for context",
            " • ↑ / ↓           Navigate command history",
            " • esc + c         Open the context panel",
        ]

    @staticmethod
    def generate_session_info(
        current_mode: OperationMode,
        working_dir: Optional[Path] = None,
        username: Optional[str] = None,
    ) -> List[str]:
        """Generate current session information."""

        cwd_path = working_dir or Path.cwd()
        cwd_display = WelcomeMessage._shorten_path(cwd_path, WelcomeMessage.LEFT_WIDTH)

        user = username or os.getenv("USER", "Developer")
        user_display = user.strip() or "Developer"

        mode = current_mode.value.upper()
        mode_desc = (
            "Plan mode · explore safely"
            if current_mode == OperationMode.PLAN
            else "Normal mode · approvals required"
        )

        return [
            "Workspace",
            cwd_display,
            "",
            f"Mode: {mode}",
            mode_desc,
            "",
            f"Signed in as {user_display}",
        ]

    @classmethod
    def generate_full_welcome(
        cls,
        current_mode: OperationMode,
        working_dir: Optional[Path] = None,
        username: Optional[str] = None,
    ) -> List[str]:
        """Generate a full welcome banner inspired by Claude Code with ANSI colors."""

        version = cls.get_version()
        working_dir = working_dir or Path.cwd()
        user = username or os.getenv("USER", "Developer")
        user_display = user.strip() or "Developer"

        # ANSI color codes for styling
        CYAN = "\033[36m"
        YELLOW = "\033[33m"
        GREEN = "\033[32m"
        BOLD = "\033[1m"
        DIM = "\033[2m"
        RESET = "\033[0m"

        # Mode color
        mode_color = GREEN if current_mode == OperationMode.PLAN else YELLOW

        left_entries: List[Tuple[str, str]] = [
            ("", "left"),
            (f"{BOLD}{CYAN}Welcome back {user_display}!{RESET}", "center"),
            ("", "left"),
            (f"{CYAN}╔═══════════╗{RESET}", "center"),
            (f"{CYAN}║  {BOLD}SWE-CLI{RESET}{CYAN}  ║{RESET}", "center"),
            (f"{CYAN}╚═══════════╝{RESET}", "center"),
            ("", "left"),
            (f"{BOLD}Workspace{RESET}", "left"),
            (f"{DIM}{cls._shorten_path(working_dir, cls.LEFT_WIDTH)}{RESET}", "left"),
            ("", "left"),
            (f"{BOLD}Mode:{RESET} {mode_color}{current_mode.value.upper()}{RESET}", "left"),
            (
                f"{DIM}Plan mode · explore safely{RESET}"
                if current_mode == OperationMode.PLAN
                else f"{DIM}Normal mode · approvals required{RESET}",
                "left",
            ),
            ("", "left"),
            (f"{DIM}Version {version}{RESET}", "left"),
            (f"{DIM}AI-powered coding assistant ready.{RESET}", "left"),
        ]

        right_entries: List[Tuple[str, str]] = [
            ("", "left"),
            (f"{BOLD}Quick Commands{RESET}", "left"),
            (f" • {CYAN}/help{RESET}           Show available commands", "left"),
            (f" • {CYAN}/tree{RESET}           Explore the project tree", "left"),
            (f" • {CYAN}/mode normal{RESET}    Run with approvals", "left"),
            (f" • {CYAN}/mode plan{RESET}      Plan without execution", "left"),
            ("", "left"),
            (f"{BOLD}Keyboard Shortcuts{RESET}", "left"),
            (f" • {YELLOW}Shift+Tab{RESET}       Toggle plan/normal mode", "left"),
            (f" • {YELLOW}@file{RESET}           Mention a file for context", "left"),
            (f" • {YELLOW}↑ / ↓{RESET}           Navigate command history", "left"),
            (f" • {YELLOW}esc + c{RESET}         Open the context panel", "left"),
            ("", "left"),
            (f"{BOLD}Pro Tips{RESET}", "left"),
            (f" • {CYAN}/save session{RESET}   Capture the current transcript", "left"),
            (f" • {YELLOW}esc + n{RESET}         Notification shortcuts", "left"),
        ]

        rows: List[str] = []
        for (left_text, left_align), (right_text, right_align) in zip_longest(
            left_entries,
            right_entries,
            fillvalue=("", "left"),
        ):
            rows.append(
                cls._two_column(
                    left_text,
                    right_text,
                    left_align=left_align,
                    right_align=right_align,
                )
            )

        return [
            "",
            cls._header_line(f"SWE-CLI {version}"),
            *rows,
            cls._footer_line(),
        ]
