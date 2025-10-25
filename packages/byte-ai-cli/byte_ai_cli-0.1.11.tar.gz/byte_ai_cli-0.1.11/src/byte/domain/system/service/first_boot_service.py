import shutil
from pathlib import Path
from typing import Literal, Optional

import yaml
from rich.console import Console
from rich.theme import Theme

from byte.core.config.config import BYTE_CACHE_DIR, BYTE_CONFIG_FILE, ByteConfg
from byte.domain.cli.rich.menu import Menu
from byte.domain.cli.schemas import ByteTheme, ThemeRegistry
from byte.domain.llm.config import LLMConfig


class FirstBootService:
	"""Handle first-time setup and configuration for Byte.

	Detects if this is the first run and guides users through initial
	configuration, creating necessary files and directories.
	Usage: `initializer = FirstBootInitializer()`
			`await initializer.run_if_needed()`
	"""

	_console: Console | None = None

	def is_first_boot(self) -> bool:
		"""Check if this is the first time Byte is being run.

		Usage: `if await initializer.is_first_boot(): ...`
		"""
		return not BYTE_CONFIG_FILE.exists()

	def run_if_needed(self) -> bool:
		"""Run initialization flow if this is the first boot.

		Returns True if initialization was performed, False if skipped.
		Usage: `initialized = await initializer.run_if_needed()`
		"""
		if not self.is_first_boot():
			return False

		self._run_initialization()
		return True

	def _run_initialization(self) -> None:
		"""Perform first-boot initialization steps.

		Creates the default configuration file from the template.
		"""

		# Load the selected Catppuccin theme variant.
		theme_registry = ThemeRegistry()
		selected_theme: ByteTheme = theme_registry.get_theme("mocha")

		init_theme = Theme(
			{
				"text": selected_theme.base05,  # Default Foreground
				"success": selected_theme.base0B,  # Green - Strings, Inserted
				"error": selected_theme.base08,  # Red - Variables, Tags
				"warning": selected_theme.base0A,  # Yellow - Classes, Bold
				"info": selected_theme.base0C,  # Teal - Support, Regex
				"danger": selected_theme.base08,  # Red - Variables, Tags
				"primary": selected_theme.base0D,  # Blue - Functions, Headings
				"secondary": selected_theme.base0E,  # Mauve - Keywords, Italic
				"muted": selected_theme.base03,  # Comments, Invisibles
				"subtle": selected_theme.base04,  # Dark Foreground
				"active_border": selected_theme.base07,  # Light Background
				"inactive_border": selected_theme.base03,  # Comments, Invisibles
			}
		)

		self._console = Console(theme=init_theme)

		# Display welcome message for first boot
		self.print_info("\n[bold cyan]Welcome to Byte![/bold cyan]")
		self.print_info("Setting up your development environment...\n")

		# Set up all Byte directories
		self._setup_byte_directories()

		# Initialize LLM configuration
		llm_model = self._init_llm()

		# Build config with selected LLM model
		config = ByteConfg()
		config.llm.model = llm_model

		# Initialize files configuration
		config = self._init_files(config)

		# Initialize web configuration
		config = self._init_web(config)

		# Write the configuration template to the YAML file
		with open(BYTE_CONFIG_FILE, "w") as f:
			yaml.dump(
				config.model_dump(mode="json"),
				f,
				default_flow_style=False,
				sort_keys=False,
				allow_unicode=True,
			)

		self.print_success(f"Created configuration file at {BYTE_CONFIG_FILE}\n")

	def _setup_byte_directories(self) -> None:
		"""Set up all necessary Byte directories.

		Creates .byte, .byte/conventions, and .byte/cache directories.
		Usage: `initializer._setup_byte_directories()`
		"""

		# Ensure the main .byte directory exists
		BYTE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

		# Create conventions directory for style guides and project conventions
		conventions_dir = BYTE_CONFIG_FILE.parent / "conventions"
		conventions_dir.mkdir(exist_ok=True)

		# Create context directory for style guides and project context
		context_dir = BYTE_CONFIG_FILE.parent / "context"
		context_dir.mkdir(exist_ok=True)

		# Create cache directory for temporary files
		BYTE_CACHE_DIR.mkdir(exist_ok=True)

		self.print_success("Created Byte directories")

	def _init_llm(self) -> Literal["anthropic", "gemini", "openai"]:
		"""Initialize LLM configuration by asking user to choose a provider.

		Only shows providers that are enabled (have API keys set).
		Returns the selected provider name.
		Usage: `model = initializer._init_llm()` -> "anthropic"
		"""
		# Create temporary LLMConfig to detect which providers are enabled
		llm_config = LLMConfig()

		# Build list of enabled providers
		enabled_providers = []
		if llm_config.anthropic.enabled:
			enabled_providers.append("anthropic")
		if llm_config.gemini.enabled:
			enabled_providers.append("gemini")
		if llm_config.openai.enabled:
			enabled_providers.append("openai")

		# If no providers are enabled, this shouldn't happen due to LLMConfig validation
		# but handle it gracefully
		if not enabled_providers:
			self.print_error("No LLM providers detected. Please set an API key environment variable.")
			return "anthropic"

		# If only one provider is enabled, use it automatically
		if len(enabled_providers) == 1:
			selected = enabled_providers[0]
			self.print_success(f"Using {selected} as LLM provider\n")
			return selected

		# Multiple providers available - ask user to choose
		self.print_info("Multiple LLM providers detected. Please choose one:\n")
		menu = Menu(*enabled_providers, title="Select LLM Provider", console=self._console)
		selected = menu.select()

		if selected is None:
			# User cancelled - default to first available
			selected = enabled_providers[0]
			self.print_warning(f"No selection made, defaulting to {selected}\n")
		else:
			self.print_success(f"Selected {selected} as LLM provider\n")

		return selected

	def _init_web(self, config: ByteConfg) -> ByteConfg:
		"""Initialize web configuration by detecting Chrome or Chromium binary.

		Attempts to locate google-chrome-stable first, then falls back to chromium.
		Updates the chrome_binary_location in the web config section.
		Usage: `config = initializer._init_web(config)`
		"""
		chrome_path = self.find_binary("google-chrome-stable")
		if chrome_path is None:
			chrome_path = self.find_binary("chromium")

		if chrome_path is not None:
			config.web.chrome_binary_location = chrome_path
			config.web.enable = True
			browser_name = "Chrome" if "chrome" in str(chrome_path) else "Chromium"
			self.print_success(f"Found {browser_name} at {chrome_path}")
			self.print_success("Web commands enabled\n")
		else:
			self.print_warning("Chromium binary not found")
			self.print_warning("Web commands are disabled\n")

		return config

	def _init_files(self, config: ByteConfg) -> ByteConfg:
		"""Initialize files configuration by asking if user wants to enable file watching.

		Prompts user with a confirmation dialog. If confirmed, sets watch.enable to true.
		Usage: `config = initializer._init_files(config)`
		"""

		menu = Menu(title="Enable file watching for AI comment markers (AI:, AI@, AI?, AI!)?", console=self._console)
		enable_watch = menu.confirm(default=False)

		if enable_watch:
			config.files.watch.enable = True
			self.print_success("File watching enabled\n")
		else:
			config.files.watch.enable = False
			self.print_info("File watching disabled\n")

		return config

	def find_binary(self, binary_name: str) -> Optional[Path]:
		"""Find the full path to a binary using which.

		Returns the absolute path to the binary if found, None otherwise.
		Usage: `chrome_path = initializer.find_binary("google-chrome")`
		Usage: `python_path = initializer.find_binary("python3")` -> Path("/usr/bin/python3")
		"""
		result = shutil.which(binary_name)
		return Path(result) if result else None

	def print_info(self, message: str) -> None:
		"""Print an informational message with two leading spaces for alignment.

		Usage: `initializer.print_info("Configuring settings...")`
		"""
		if self._console:
			self._console.print(f"  {message}")

	def print_success(self, message: str) -> None:
		"""Print a success message with a green checkmark.

		Usage: `initializer.print_success("Configuration saved")`
		"""
		if self._console:
			self._console.print(f"[green]✓[/green] {message}")

	def print_error(self, message: str) -> None:
		"""Print an error message with a red X.

		Usage: `initializer.print_error("Failed to save configuration")`
		"""
		if self._console:
			self._console.print(f"[red]✗[/red] {message}")

	def print_warning(self, message: str) -> None:
		"""Print a warning message with a yellow exclamation mark.

		Usage: `initializer.print_warning("Chrome not found, web commands disabled")`
		"""
		if self._console:
			self._console.print(f"[yellow]⚠[/yellow] {message}")
