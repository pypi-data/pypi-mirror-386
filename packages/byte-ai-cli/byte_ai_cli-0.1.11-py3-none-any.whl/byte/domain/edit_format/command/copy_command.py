from byte.core.mixins.user_interactive import UserInteractive
from byte.domain.agent.implementations.copy.agent import CopyAgent
from byte.domain.cli.service.command_registry import Command


class CopyCommand(Command, UserInteractive):
	"""Command to copy code blocks from the last AI message to clipboard.

	Extracts all code blocks from the most recent assistant response,
	displays truncated previews, and allows user selection for copying.
	Usage: `/copy` in the CLI
	"""

	@property
	def name(self) -> str:
		return "copy"

	@property
	def description(self) -> str:
		return "Copy code blocks from the last message to clipboard"

	async def execute(self, args: str) -> None:
		"""Execute the copy command by running the CopyAgent.

		Args:
			args: Command arguments (unused)

		Usage: User types `/copy` in the interactive CLI
		"""
		copy_agent = await self.make(CopyAgent)
		await copy_agent.execute(
			{},
			display_mode="silent",
		)
