import click

from .cmd_files import cli as files
from .cmd_formulae import cli as formulae


@click.group(
    "extract",
    short_help="Extract information like formulae and files from a DCC XML file.",
)
def cli():
    pass


cli.add_command(formulae, "formulae")
cli.add_command(files, "files")
