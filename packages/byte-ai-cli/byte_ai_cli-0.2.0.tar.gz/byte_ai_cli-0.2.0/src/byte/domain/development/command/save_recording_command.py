from rich import terminal_theme
from rich.console import Console

from byte.core.config.config import ByteConfg
from byte.domain.cli.service.command_registry import Command


class SaveRecordingCommand(Command):
	""" """

	@property
	def name(self) -> str:
		return "dev:rec:save"

	@property
	def description(self) -> str:
		return ""

	async def execute(self, args: str) -> None:
		""" """
		config = await self.make(ByteConfg)
		console = await self.make(Console)
		console.save_svg(
			str(config.project_root / "docs" / "images" / f"{args}.svg"),
			title="",
			theme=terminal_theme.MONOKAI,
		)
		console.record = False
