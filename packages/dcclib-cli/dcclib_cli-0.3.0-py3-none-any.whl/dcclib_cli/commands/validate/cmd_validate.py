import click

from .cmd_schematron import cli as schematron
from .cmd_xsd import cli as xsd


@click.group(
    "validate",
    short_help="Validate an DCC XML file against the DCC schema and schematron.",
)
def cli():
    pass


cli.add_command(schematron, "schematron")
cli.add_command(xsd, "xsd")
