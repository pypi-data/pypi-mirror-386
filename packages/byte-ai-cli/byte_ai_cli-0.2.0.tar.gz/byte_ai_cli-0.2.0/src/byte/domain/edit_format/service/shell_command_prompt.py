from textwrap import dedent

# From: https://github.com/Aider-AI/aider/blob/f8aa80396d9696111c93f6f34adbf10347c59a1a/aider/coders/shell.py
shell_command_system = dedent("""
		# *Shell Command Block* Rules:
		Use *Shell Command blocks* to execute shell commands AFTER file edits are applied.

		Just suggest shell commands this way, not example code.
		Only suggest complete shell commands that are ready to execute, without placeholders.
		Only suggest at most a few shell commands at a time, not more than 1-3, one per line.
		Do not suggest multi-line shell commands.
		All shell commands will run from the root directory of the user's project.

		## Block Format:

		```sh
		command to execute
		```
		Or:
		```bash
		command to execute
		second command to execute
		```

		## **CRITICAL RULES:**

		When to Use:
		- If you changed a CLI program, suggest the command to run it to see the new behavior.
		- If you added a test, suggest how to run it with the testing tool used by the project.
		- If your code changes add new dependencies, suggest the command to install them.
		- Never edit files with shell commands (echo, sed, >>) - use SEARCH/REPLACE instead

		Safety:
		- Commands require user confirmation before execution
		- Dangerous operations prompt for explicit approval

		Execution:
		- Execute AFTER all SEARCH/REPLACE blocks succeed
		- Execute sequentially in order they appear
		- If file edits fail, shell commands are skipped""")

shell_practice_messages = [
	(
		"user",
		"Update the calculator and run the tests",
	),
	(
		"assistant",
		dedent("""
		I'll update the calculator function and then run the test suite:

		```python
		+++++++ calculator.py
		<<<<<<< SEARCH
		def add(a, b):
			return a + b
		=======
		def add(a: int, b: int) -> int:
			\"\"\"Add two integers and return the result.\"\"\"
			return a + b
		>>>>>>> REPLACE
		```

		Now let's verify the changes:
		```sh
		pytest tests/test_calculator.py -v
		```"""),
	),
	(
		"user",
		"Create a new config file and install the dependencies",
	),
	(
		"assistant",
		dedent("""
		I'll create the config file and then install dependencies:
		```python
		+++++++ config.py
		<<<<<<< SEARCH
		=======
		import os
		from dataclasses import dataclass

		@dataclass
		class Config:
			debug: bool = False
			port: int = 8000
		>>>>>>> REPLACE
		```

		Now installing dependencies:
		```bash
		uv sync
		```"""),
	),
]
