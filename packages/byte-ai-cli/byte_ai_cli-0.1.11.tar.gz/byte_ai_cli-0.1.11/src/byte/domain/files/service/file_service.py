import glob
from os import PathLike
from pathlib import Path
from typing import Dict, List, Optional, Union

from rich.columns import Columns

from byte.core.event_bus import EventType, Payload
from byte.core.service.base_service import Service
from byte.domain.cli.service.console_service import ConsoleService
from byte.domain.files.schemas import FileContext, FileMode
from byte.domain.files.service.discovery_service import FileDiscoveryService


class FileService(Service):
	"""Simplified domain service for file context management with project discovery.

	Manages the active set of files available to the AI assistant, with
	integrated project file discovery for better completions and file operations.
	Loads all project files on boot for fast reference and completion.
	Usage: `await file_service.add_file("main.py", FileMode.EDITABLE)`
	"""

	async def boot(self) -> None:
		"""Initialize file service and ensure discovery service is ready."""
		self._context_files: Dict[str, FileContext] = {}

	async def add_file(self, path: Union[str, PathLike], mode: FileMode) -> bool:
		"""Add a file to the active context for AI awareness.

		Supports wildcard patterns like 'byte/*' to add multiple files at once.
		Only adds files that are available in the FileDiscoveryService to ensure
		they are valid project files that respect gitignore patterns.
		Usage: `await service.add_file("config.py", FileMode.READ_ONLY)`
		Usage: `await service.add_file("src/*.py", FileMode.EDITABLE)` -> adds all Python files
		"""
		console = await self.make(ConsoleService)
		file_discovery = await self.make(FileDiscoveryService)
		discovered_files = await file_discovery.get_files()
		discovered_file_paths = {str(f.resolve()) for f in discovered_files}

		path_str = str(path)

		# Check if path contains wildcard patterns
		if "*" in path_str or "?" in path_str or "[" in path_str:
			# Handle glob patterns
			matching_paths = glob.glob(path_str, recursive=True)
			if not matching_paths:
				return False

			success_count = 0
			for match_path in matching_paths:
				path_obj = Path(match_path).resolve()

				# Only add files that are in the discovery service and are actual files
				if path_obj.is_file() and str(path_obj) in discovered_file_paths:
					key = str(path_obj)
					self._context_files[key] = FileContext(path=path_obj, mode=mode)

					# Print the file that was added
					relative_path = (
						str(path_obj.relative_to(self._config.project_root))
						if self._config.project_root
						else str(path_obj)
					)
					mode_str = "editable" if mode == FileMode.EDITABLE else "read-only"
					console.print(f"[text]Added {relative_path} ({mode_str})[/text]")

					success_count += 1

			return success_count > 0
		else:
			# Handle single file path
			path_obj = Path(path).resolve()

			# Only add if file is in the discovery service
			if not path_obj.is_file() or str(path_obj) not in discovered_file_paths:
				return False

			key = str(path_obj)

			# If the file is already in context, return False
			if key in self._context_files:
				return False

			self._context_files[key] = FileContext(path=path_obj, mode=mode)

			# Print the file that was added
			relative_path = (
				str(path_obj.relative_to(self._config.project_root)) if self._config.project_root else str(path_obj)
			)
			mode_str = "editable" if mode == FileMode.EDITABLE else "read-only"
			console.print(f"[text]Added {relative_path} ({mode_str})[/text]")

			await self._notify_file_added(key, mode)

			# Emit event for UI updates and other interested components
			return True

	async def _notify_file_added(self, file_path: str, mode: FileMode):
		"""Notify system that a file was added to context"""

		payload = Payload(
			event_type=EventType.FILE_ADDED,
			data={
				"file_path": file_path,
				"mode": mode.value,
				"action": "context_added",
			},
		)

		await self.emit(payload)

	async def remove_file(self, path: Union[str, PathLike]) -> bool:
		"""Remove a file from active context to reduce noise.

		Supports wildcard patterns like 'byte/*' to remove multiple files at once.
		Only removes files that are available in the FileDiscoveryService to ensure
		consistency with project file management.
		Usage: `await service.remove_file("old_file.py")`
		Usage: `await service.remove_file("src/*.py")` -> removes all Python files
		"""
		file_discovery = await self.make(FileDiscoveryService)
		discovered_files = await file_discovery.get_files()
		discovered_file_paths = {str(f.resolve()) for f in discovered_files}

		path_str = str(path)

		# Check if path contains wildcard patterns
		if "*" in path_str or "?" in path_str or "[" in path_str:
			# Handle glob patterns - match against files currently in context
			matching_paths = []
			for context_path in list(self._context_files.keys()):
				# Only consider files that are in the discovery service
				if context_path not in discovered_file_paths:
					continue

				# Convert absolute path back to relative for pattern matching
				try:
					relative_path = str(Path(context_path).relative_to(Path.cwd()))
					if glob.fnmatch.fnmatch(relative_path, path_str) or glob.fnmatch.fnmatch(context_path, path_str):  # pyright: ignore[reportAttributeAccessIssue]
						matching_paths.append(context_path)
				except ValueError:
					# If can't make relative, try matching absolute path
					if glob.fnmatch.fnmatch(context_path, path_str):  # pyright: ignore[reportAttributeAccessIssue]
						matching_paths.append(context_path)

			if not matching_paths:
				return False

			# Remove all matching files
			for match_path in matching_paths:
				del self._context_files[match_path]
				# await self.event(FileRemoved(file_path=match_path))

			return True
		else:
			# Handle single file path
			path_obj = Path(path).resolve()
			key = str(path_obj)

			# Only remove if file is in context and in discovery service
			if key in self._context_files and key in discovered_file_paths:
				del self._context_files[key]
				# await self.event(FileRemoved(file_path=str(path_obj)))
				return True
			return False

	def list_files(self, mode: Optional[FileMode] = None) -> List[FileContext]:
		"""List files in context, optionally filtered by access mode.

		Enables UI components to display current context state and
		distinguish between editable and read-only files.
		Usage: `editable_files = service.list_files(FileMode.EDITABLE)`
		"""
		files = list(self._context_files.values())

		if mode is not None:
			files = [f for f in files if f.mode == mode]

		# Sort by relative path for consistent, user-friendly ordering
		return sorted(files, key=lambda f: f.relative_path)

	# TODO: This needs to be completed and added as a command
	async def set_file_mode(self, path: Union[str, PathLike], mode: FileMode) -> bool:
		"""Change file access mode between read-only and editable.

		Allows users to adjust file permissions without removing and re-adding,
		useful when transitioning from exploration to editing phases.
		Usage: `await service.set_file_mode("main.py", FileMode.EDITABLE)`
		"""
		path_obj = Path(path).resolve()
		key = str(path_obj)

		if key in self._context_files:
			self._context_files[key].mode = mode
			return True
		return False

	def get_file_context(self, path: Union[str, PathLike]) -> Optional[FileContext]:
		"""Retrieve file context metadata for a specific path.

		Provides access to file mode and other metadata without reading
		the full file content, useful for UI state management.
		Usage: `context = service.get_file_context("main.py")`
		"""
		path_obj = Path(path).resolve()
		return self._context_files.get(str(path_obj))

	async def generate_context_prompt(self) -> tuple[list[str], list[str]]:
		"""Generate structured file lists for read-only and editable files.

		Returns two separate lists of formatted file strings, enabling
		flexible assembly in the prompt context. The AI can understand
		its permissions and make appropriate suggestions for each file type.

		Returns:
			Tuple of (read_only_files, editable_files) as lists of strings

		Usage: `read_only, editable = await service.generate_context_prompt()`
		"""
		read_only_files = []
		editable_files = []

		if not self._context_files:
			return (read_only_files, editable_files)

		# Separate files by mode for clear AI understanding
		read_only = [f for f in self._context_files.values() if f.mode == FileMode.READ_ONLY]
		editable = [f for f in self._context_files.values() if f.mode == FileMode.EDITABLE]

		if read_only:
			for file_ctx in sorted(read_only, key=lambda f: f.relative_path):
				content = file_ctx.get_content()
				if content is not None:
					content = await self._emit_file_context_event(file_ctx.relative_path, FileMode.READ_ONLY, content)
					read_only_files.append(
						f"""<file: source={file_ctx.relative_path}, mode=read-only>\n{content}\n</file>"""
					)

		if editable:
			for file_ctx in sorted(editable, key=lambda f: f.relative_path):
				content = file_ctx.get_content()
				if content is not None:
					content = await self._emit_file_context_event(file_ctx.relative_path, FileMode.EDITABLE, content)
					editable_files.append(
						f"""<file: source={file_ctx.relative_path}, mode=editable>\n{content}\n</file>"""
					)

		return (read_only_files, editable_files)

	async def _emit_file_context_event(self, file: str, type, content: str) -> str:
		""" """
		payload = Payload(
			event_type=EventType.GENERATE_FILE_CONTEXT,
			data={
				"file": file,
				"type": type,
				"content": content,
			},
		)

		payload = await self.emit(payload)
		return payload.get("content", content)

	async def clear_context(self):
		"""Clear all files from context for fresh start.

		Useful when switching tasks or when context becomes too large
		for effective AI processing, enabling a clean slate approach.
		Usage: `await service.clear_context()` -> empty context
		"""
		self._context_files.clear()

	# Project file discovery methods
	async def get_project_files(self, extension: Optional[str] = None) -> List[str]:
		"""Get all project files as relative path strings.

		Uses the discovery service to provide fast access to all project files,
		optionally filtered by extension for language-specific operations.
		Usage: `py_files = service.get_project_files('.py')` -> Python files
		"""
		file_discovery = await self.make(FileDiscoveryService)
		return await file_discovery.get_relative_paths(extension)

	async def find_project_files(self, pattern: str) -> List[str]:
		"""Find project files matching a pattern for completions.

		Provides fast file path completion by searching the cached project
		file index, respecting gitignore patterns automatically.
		Usage: `matches = service.find_project_files('src/main')` -> matching files
		"""
		file_discovery = await self.make(FileDiscoveryService)
		matches = await file_discovery.find_files(pattern)

		if not self._config.project_root:
			return [str(f) for f in matches]
		return [str(f.relative_to(self._config.project_root)) for f in matches]

	async def is_file_in_context(self, path: Union[str, PathLike]) -> bool:
		"""Check if a file is currently in the AI context.

		Quick lookup to determine if a file is already being tracked,
		useful for command validation and UI state management.
		Usage: `in_context = service.is_file_in_context("main.py")`
		"""
		path_obj = Path(path).resolve()
		return str(path_obj) in self._context_files

	async def list_in_context_files_hook(self, payload: Payload):
		"""Display current editable files before each prompt.

		Provides visual feedback about which files the AI can modify,
		helping users understand the current context state.
		"""

		console = await self.make(ConsoleService)

		info_panel = payload.get("info_panel", [])

		read_only_panel = None

		file_service = await self.make(FileService)
		readonly_files = file_service.list_files(FileMode.READ_ONLY)
		if readonly_files:
			file_names = [f"[text]{f.relative_path}[/text]" for f in readonly_files]
			read_only_panel = console.panel(
				Columns(file_names, equal=True, expand=True),
				title=f"Read-only Files ({len(readonly_files)})",
			)

		editable_panel = None
		editable_files = file_service.list_files(FileMode.EDITABLE)
		if editable_files:
			file_names = [f"[text]{f.relative_path}[/text]" for f in editable_files]
			editable_panel = console.panel(
				Columns(file_names, equal=True, expand=True),
				title=f"Editable Files ({len(editable_files)})",
			)

		# Create columns layout with both panels if they exist
		panels_to_show = []
		if read_only_panel:
			panels_to_show.append(read_only_panel)
		if editable_panel:
			panels_to_show.append(editable_panel)

		if panels_to_show:
			columns_panel = Columns(panels_to_show, equal=True, expand=True)
			info_panel.append(columns_panel)

		return payload.set("info_panel", info_panel)

	async def add_file_context_to_prompt_hook(self, payload: Optional[Payload] = None):
		"""Add file context to the payload for prompt assembly.

		Generates separate lists for read-only and editable files and adds
		them to the payload data, avoiding direct state manipulation.

		Usage: `payload = await service.add_file_context_to_prompt_hook(payload)`
		"""
		if payload:
			read_only_files, editable_files = await self.generate_context_prompt()
			payload.set("read_only", read_only_files)
			payload.set("editable", editable_files)

		return payload
