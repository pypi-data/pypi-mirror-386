import click

from byte.core.config.config import ByteConfg
from byte.core.initializer import FirstBootInitializer


@click.command()
def cli():
	"""Byte CLI Assistant"""
	from byte.main import run

	# Check for first boot before bootstrapping
	initializer = FirstBootInitializer()
	if initializer.is_first_boot():
		initializer.run_if_needed()

	config = ByteConfg()
	run(config)


if __name__ == "__main__":
	cli()
