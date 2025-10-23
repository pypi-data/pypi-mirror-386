from typing import List, Type

from byte.container import Container
from byte.core.event_bus import EventBus, EventType
from byte.core.service.base_service import Service
from byte.core.service_provider import ServiceProvider
from byte.domain.cli.service.command_registry import Command
from byte.domain.cli.service.console_service import ConsoleService
from byte.domain.files.command.add_file_command import AddFileCommand
from byte.domain.files.command.add_read_only_file_command import ReadOnlyCommand
from byte.domain.files.command.drop_file_command import DropFileCommand
from byte.domain.files.command.list_files_command import ListFilesCommand
from byte.domain.files.service.discovery_service import FileDiscoveryService
from byte.domain.files.service.file_service import FileService
from byte.domain.files.service.ignore_service import FileIgnoreService
from byte.domain.files.service.watcher_service import FileWatcherService


class FileServiceProvider(ServiceProvider):
	"""Service provider for simplified file functionality with project discovery."""

	def services(self) -> List[Type[Service]]:
		return [
			FileIgnoreService,
			FileDiscoveryService,
			FileService,
			FileWatcherService,
		]

	def commands(self) -> List[Type[Command]]:
		return [ListFilesCommand, AddFileCommand, ReadOnlyCommand, DropFileCommand]

	async def boot(self, container: Container):
		"""Boot file services and register commands with registry."""
		# Ensure ignore service is booted first for pattern loading
		await container.make(FileIgnoreService)

		# Then boot file discovery which depends on ignore service
		file_discovery = await container.make(FileDiscoveryService)

		# Boots the filewatcher service in to the task manager
		file_watcher_service = await container.make(FileWatcherService)

		# Set up event listener for PRE_PROMPT_TOOLKIT
		event_bus = await container.make(EventBus)
		file_service = await container.make(FileService)

		# Register listener that calls list_in_context_files before each prompt
		event_bus.on(
			EventType.PRE_PROMPT_TOOLKIT.value,
			file_service.list_in_context_files_hook,
		)

		event_bus.on(
			EventType.GATHER_FILE_CONTEXT.value,
			file_service.add_file_context_to_prompt_hook,
		)

		event_bus.on(
			EventType.POST_PROMPT_TOOLKIT.value,
			file_watcher_service.modify_user_request_hook,
		)

		# Register listener that calls list_in_context_files before each prompt
		event_bus.on(
			EventType.GATHER_REINFORCEMENT.value,
			file_watcher_service.add_reinforcement_hook,
		)

		console = await container.make(ConsoleService)

		found_files = await file_discovery.get_files()
		console.print(f"│ [success]Discovered:[/success] [info]{len(found_files)} files[/info]")
		console.print("│ ", style="text")
