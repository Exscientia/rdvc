import click
from rdvc._version import version
from rdvc.cli_options import get_cli_defaults
from rdvc.commands.init import init
from rdvc.commands.queue import queue
from rdvc.commands.run import run


@click.group(context_settings={"default_map": get_cli_defaults()})
@click.version_option(version)
def cli() -> None:
    """Remote execution of DVC pipelines on a SLURM cluster."""


cli.add_command(init)
cli.add_command(run)
cli.add_command(queue)
