"""Notification center for SWE-CLI."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, List, Sequence

from rich.console import Console
from rich.table import Table


@dataclass
class Notification:
    """Notification model stored in the center."""

    timestamp: datetime
    level: str
    message: str

    def summary(self) -> str:
        """Return a short human readable summary."""
        time_str = self.timestamp.strftime("%H:%M:%S")
        level_marker = {
            "info": "ℹ",
            "warning": "⚠",
            "error": "✗",
        }.get(self.level, "•")
        return f"{level_marker} {time_str} {self.message}"


class NotificationCenter:
    """Collect and render notifications for the REPL."""

    def __init__(self, console: Console, max_items: int = 50) -> None:
        self.console = console
        self._items: Deque[Notification] = deque(maxlen=max_items)

    def add(self, level: str, message: str) -> Notification:
        """Record a new notification."""
        entry = Notification(timestamp=datetime.now(), level=level, message=message)
        self._items.appendleft(entry)
        return entry

    def latest(self, limit: int = 3) -> List[Notification]:
        """Return newest notifications (head of deque)."""
        return list(list(self._items)[:limit])

    def render(self, limit: Union[int, None] = None) -> None:
        """Render the notification table to the console."""
        if not self._items:
            self.console.print("[dim]No notifications yet.[/dim]")
            return

        rows: Sequence[Notification] = self._items if limit is None else list(self._items)[:limit]

        table = Table(title="Notification Center", header_style="bold cyan")
        table.add_column("Time", style="dim", width=9)
        table.add_column("Level", style="magenta", width=8)
        table.add_column("Message", overflow="fold")

        for notification in rows:
            table.add_row(
                notification.timestamp.strftime("%H:%M:%S"),
                notification.level.capitalize(),
                notification.message,
            )

        self.console.print(table)

    def has_items(self) -> bool:
        """Return True when notifications exist."""
        return bool(self._items)
