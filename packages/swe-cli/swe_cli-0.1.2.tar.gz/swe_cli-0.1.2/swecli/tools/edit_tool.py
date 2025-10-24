"""Tool for editing existing files."""

import re
import shutil
from pathlib import Path
from typing import Optional

from swecli.models.config import AppConfig
from swecli.models.operation import EditResult, Operation
from swecli.tools.base import BaseTool
from swecli.tools.diff_preview import DiffPreview, Diff


class EditTool(BaseTool):
    """Tool for editing existing files with diff preview."""

    @property
    def name(self) -> str:
        """Tool name."""
        return "edit_file"

    @property
    def description(self) -> str:
        """Tool description."""
        return "Edit an existing file with search and replace"

    def __init__(self, config: AppConfig, working_dir: Path):
        """Initialize edit tool.

        Args:
            config: Application configuration
            working_dir: Working directory for operations
        """
        self.config = config
        self.working_dir = working_dir
        self.diff_preview = DiffPreview()

    def edit_file(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
        match_all: bool = False,
        dry_run: bool = False,
        backup: bool = True,
        operation: Optional[Operation] = None,
    ) -> EditResult:
        """Edit file by replacing old_content with new_content.

        Args:
            file_path: Path to file to edit
            old_content: Content to find and replace
            new_content: New content to insert
            match_all: Replace all occurrences (default: first only)
            dry_run: If True, don't actually modify file
            backup: Create backup before editing
            operation: Operation object for tracking

        Returns:
            EditResult with operation details

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If edit is not permitted
            ValueError: If old_content not found or not unique
        """
        # Resolve path
        path = self._resolve_path(file_path)

        # Check if file exists
        if not path.exists():
            error = f"File not found: {path}"
            if operation:
                operation.mark_failed(error)
            return EditResult(
                success=False,
                file_path=str(path),
                lines_added=0,
                lines_removed=0,
                error=error,
                operation_id=operation.id if operation else None,
            )

        # Check write permissions
        if not self.config.permissions.file_write.is_allowed(str(path)):
            error = f"Editing {path} is not permitted by configuration"
            if operation:
                operation.mark_failed(error)
            return EditResult(
                success=False,
                file_path=str(path),
                lines_added=0,
                lines_removed=0,
                error=error,
                operation_id=operation.id if operation else None,
            )

        try:
            # Read original content
            with open(path, "r", encoding="utf-8") as f:
                original = f.read()

            # Check if old_content exists
            if old_content not in original:
                error = f"Content not found in file: {old_content[:50]}..."
                if operation:
                    operation.mark_failed(error)
                return EditResult(
                    success=False,
                    file_path=str(path),
                    lines_added=0,
                    lines_removed=0,
                    error=error,
                    operation_id=operation.id if operation else None,
                )

            # Check if old_content is unique (if not match_all)
            if not match_all and original.count(old_content) > 1:
                error = f"Content appears {original.count(old_content)} times. Use match_all=True or provide more specific content"
                if operation:
                    operation.mark_failed(error)
                return EditResult(
                    success=False,
                    file_path=str(path),
                    lines_added=0,
                    lines_removed=0,
                    error=error,
                    operation_id=operation.id if operation else None,
                )

            # Perform replacement
            if match_all:
                modified = original.replace(old_content, new_content)
            else:
                modified = original.replace(old_content, new_content, 1)

            # Calculate diff statistics and textual diff
            diff = Diff(str(path), original, modified)
            stats = diff.get_stats()
            diff_text = diff.generate_unified_diff(context_lines=3)

            # Dry run - don't actually write
            if dry_run:
                return EditResult(
                    success=True,
                    file_path=str(path),
                    lines_added=stats["lines_added"],
                    lines_removed=stats["lines_removed"],
                    diff=diff_text,
                    operation_id=operation.id if operation else None,
                )

            # Mark operation as executing
            if operation:
                operation.mark_executing()

            # Create backup if requested
            backup_path = None
            if backup and self.config.operation.backup_before_edit:
                backup_path = str(path) + ".bak"
                shutil.copy2(path, backup_path)

            # Write modified content
            with open(path, "w", encoding="utf-8") as f:
                f.write(modified)

            # Mark operation as successful
            if operation:
                operation.mark_success()

            return EditResult(
                success=True,
                file_path=str(path),
                lines_added=stats["lines_added"],
                lines_removed=stats["lines_removed"],
                backup_path=backup_path,
                diff=diff_text,
                operation_id=operation.id if operation else None,
            )

        except Exception as e:
            error = f"Failed to edit file: {str(e)}"
            if operation:
                operation.mark_failed(error)
            return EditResult(
                success=False,
                file_path=str(path),
                lines_added=0,
                lines_removed=0,
                error=error,
                operation_id=operation.id if operation else None,
            )

    def edit_lines(
        self,
        file_path: str,
        line_start: int,
        line_end: int,
        new_content: str,
        dry_run: bool = False,
        backup: bool = True,
        operation: Optional[Operation] = None,
    ) -> EditResult:
        """Edit specific lines in a file.

        Args:
            file_path: Path to file
            line_start: Starting line (1-indexed, inclusive)
            line_end: Ending line (1-indexed, inclusive)
            new_content: New content for those lines
            dry_run: If True, don't actually modify file
            backup: Create backup before editing
            operation: Operation object for tracking

        Returns:
            EditResult with operation details
        """
        path = self._resolve_path(file_path)

        # Check if file exists
        if not path.exists():
            error = f"File not found: {path}"
            if operation:
                operation.mark_failed(error)
            return EditResult(
                success=False,
                file_path=str(path),
                lines_added=0,
                lines_removed=0,
                error=error,
                operation_id=operation.id if operation else None,
            )

        try:
            # Read file
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Validate line numbers
            if line_start < 1 or line_end > len(lines) or line_start > line_end:
                error = f"Invalid line range: {line_start}-{line_end} (file has {len(lines)} lines)"
                if operation:
                    operation.mark_failed(error)
                return EditResult(
                    success=False,
                    file_path=str(path),
                    lines_added=0,
                    lines_removed=0,
                    error=error,
                    operation_id=operation.id if operation else None,
                )

            # Build old and new content
            original = "".join(lines)
            old_lines = lines[line_start - 1 : line_end]
            old_content = "".join(old_lines)

            # Replace lines
            new_lines = (
                lines[: line_start - 1]
                + [new_content if not new_content.endswith("\n") else new_content]
                + lines[line_end:]
            )

            if not new_content.endswith("\n") and line_end < len(lines):
                new_lines[line_start - 1] += "\n"

            modified = "".join(new_lines)

            # Use the main edit_file method
            return self.edit_file(
                file_path=file_path,
                old_content=old_content,
                new_content=new_content if new_content.endswith("\n") else new_content + "\n",
                match_all=False,
                dry_run=dry_run,
                backup=backup,
                operation=operation,
            )

        except Exception as e:
            error = f"Failed to edit lines: {str(e)}"
            if operation:
                operation.mark_failed(error)
            return EditResult(
                success=False,
                file_path=str(path),
                lines_added=0,
                lines_removed=0,
                error=error,
                operation_id=operation.id if operation else None,
            )

    def execute(self, **kwargs) -> EditResult:
        """Execute the tool.

        Args:
            **kwargs: Arguments for edit_file

        Returns:
            EditResult
        """
        return self.edit_file(**kwargs)

    def preview_edit(
        self, file_path: str, old_content: str, new_content: str
    ) -> None:
        """Preview an edit operation.

        Args:
            file_path: Path to file
            old_content: Content to replace
            new_content: New content
        """
        path = self._resolve_path(file_path)

        # Read original
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()

        # Generate modified
        modified = original.replace(old_content, new_content, 1)

        # Display diff
        self.diff_preview.preview_edit(str(path), original, modified)

    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to working directory.

        Args:
            path: Path string (relative or absolute)

        Returns:
            Resolved Path object
        """
        p = Path(path)
        if p.is_absolute():
            return p
        return (self.working_dir / p).resolve()
