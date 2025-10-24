"""Process-oriented tool handlers (run command & process management)."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import Any

from swecli.core.tools.context import ToolExecutionContext
from swecli.models.operation import Operation, OperationType


class ProcessToolHandler:
    """Encapsulates bash execution and process monitoring tools."""

    _SERVER_PATTERNS = (
        r"flask\s+run",
        r"python.*app\.py",
        r"python.*manage\.py\s+runserver",
        r"django.*runserver",
        r"uvicorn",
        r"gunicorn",
        r"python.*-m\s+http\.server",
        r"npm\s+(run\s+)?(start|dev|serve)",
        r"yarn\s+(run\s+)?(start|dev|serve)",
        r"node.*server",
        r"nodemon",
        r"next\s+(dev|start)",
        r"rails\s+server",
        r"php.*artisan\s+serve",
        r"hugo\s+server",
        r"jekyll\s+serve",
    )

    def __init__(self, bash_tool: Any) -> None:
        self._bash_tool = bash_tool

    def run_command(self, args: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
        if not self._bash_tool:
            return {"success": False, "error": "BashTool not available"}

        command = args["command"]
        background = args.get("background", False)

        if not background and self._is_server_command(command):
            background = True

        operation = Operation(
            id=str(hash(f"{command}{datetime.now()}")),
            type=OperationType.BASH_EXECUTE,
            target=command,
            parameters={"command": command, "background": background},
            created_at=datetime.now(),
        )

        if not self._ensure_command_approval(command, background, operation, context):
            return {
                "success": False,
                "error": "Operation cancelled by user",
                "output": None,
            }

        result = self._bash_tool.execute(command, background=background, operation=operation)

        if result.success and context.undo_manager:
            context.undo_manager.record_operation(operation)

        output_parts = [part for part in (result.stdout, result.stderr) if part]
        combined_output = "\n".join(output_parts)

        if result.success:
            return {
                "success": True,
                "output": combined_output or "Command executed",
                "error": None,
            }

        error_parts = [p for p in (result.error, combined_output) if p]
        error_message = "\n".join(error_parts) if error_parts else "Command execution failed"
        return {"success": False, "output": None, "error": error_message}

    def list_processes(self) -> dict[str, Any]:
        if not self._bash_tool:
            return {"success": False, "error": "BashTool not available"}

        try:
            processes = self._bash_tool.list_processes()
            if not processes:
                output = "No background processes running"
            else:
                lines = ["Background processes:"]
                for proc in processes:
                    status_emoji = "🟢" if proc["status"] == "running" else "⚫"
                    line = (
                        f"  {status_emoji} PID {proc['pid']}: {proc['command'][:60]} "
                        f"({proc['status']}, {proc['runtime']:.1f}s)"
                    )
                    if proc["exit_code"] is not None:
                        line += f" [exit code: {proc['exit_code']}]"
                    lines.append(line)
                output = "\n".join(lines)

            return {"success": True, "output": output, "error": None}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc), "output": None}

    def get_process_output(self, args: dict[str, Any]) -> dict[str, Any]:
        if not self._bash_tool:
            return {"success": False, "error": "BashTool not available"}

        pid = args["pid"]
        try:
            result = self._bash_tool.get_process_output(pid)
            if not result["success"]:
                return {"success": False, "error": result["error"], "output": None}

            lines = [
                f"Process {pid}: {result['command'][:60]}",
                f"Status: {result['status']}",
                f"Runtime: {result['runtime']:.1f}s",
            ]
            if result["exit_code"] is not None:
                lines.append(f"Exit code: {result['exit_code']}")
            if result["stdout"]:
                lines.append(f"\nStdout:\n{result['stdout']}")
            if result["stderr"]:
                lines.append(f"\nStderr:\n{result['stderr']}")

            return {"success": True, "output": "\n".join(lines), "error": None}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc), "output": None}

    def kill_process(self, args: dict[str, Any]) -> dict[str, Any]:
        if not self._bash_tool:
            return {"success": False, "error": "BashTool not available"}

        pid = args["pid"]
        signal = args.get("signal", 15)

        try:
            result = self._bash_tool.kill_process(pid, signal)
            if not result["success"]:
                return {"success": False, "error": result["error"], "output": None}
            return {"success": True, "output": result["message"], "error": None}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc), "output": None}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_command_approval(
        self,
        command: str,
        background: bool,
        operation: Operation,
        context: ToolExecutionContext,
    ) -> bool:
        mode_manager = context.mode_manager
        if mode_manager and not mode_manager.needs_approval(operation):
            operation.approved = True
            return True

        approval_manager = context.approval_manager
        if not approval_manager:
            operation.approved = True
            return True

        if hasattr(approval_manager, "pre_approved_commands") and command in approval_manager.pre_approved_commands:
            approval_manager.pre_approved_commands.discard(command)
            operation.approved = True
            return True

        preview = f"Execute{' (background)' if background else ''}: {command}"
        working_dir = str(self._bash_tool.working_dir) if getattr(self._bash_tool, "working_dir", None) else "."

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            result = asyncio.run(
                approval_manager.request_approval(
                    operation=operation,
                    preview=preview,
                    command=command,
                    working_dir=working_dir,
                    force_prompt=True,
                )
            )
            if not result.approved:
                return False
            operation.approved = True
            return True

        operation.approved = True
        return True

    @classmethod
    def _is_server_command(cls, command: str) -> bool:
        return any(re.search(pattern, command, re.IGNORECASE) for pattern in cls._SERVER_PATTERNS)
