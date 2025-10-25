from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic.dataclasses import dataclass


class FileMode(Enum):
	"""File access mode for AI context management."""

	READ_ONLY = "read_only"
	EDITABLE = "editable"


@dataclass
class FileContext:
	"""Immutable file context containing path and access mode information."""

	path: Path
	mode: FileMode

	@property
	def relative_path(self) -> str:
		"""Get relative path string for display purposes."""
		try:
			# Try to get relative path from current working directory
			return str(self.path.relative_to(Path.cwd()))
		except ValueError:
			# If path is outside cwd, return absolute path
			return str(self.path)

	def get_content(self) -> Optional[str]:
		"""Read file content safely, returning None if unreadable."""
		try:
			return self.path.read_text(encoding="utf-8")
		except (FileNotFoundError, PermissionError, UnicodeDecodeError):
			return None
