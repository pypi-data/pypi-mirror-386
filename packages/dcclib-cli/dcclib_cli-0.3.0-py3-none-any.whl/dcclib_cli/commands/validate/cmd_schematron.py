import os
import sys

import click
from prettytable import PrettyTable

from dcclib.validation import (
    SchematronValidator,
    SchemaVersion,
    compile_schematron_to_svrl,
)

from ..output import echo_success

SCHEMA_VERSIONS = [version.name.replace("_", ".") for version in SchemaVersion]


@click.command(
    "schematron",
    short_help="Validate an DCC XML file against the DCC schematron.",
)
@click.argument("xml_file", metavar="XML_PATH", type=click.File(encoding="utf-8"))
@click.option(
    "-s",
    "--schematron",
    "schematron_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Path to the schematron file to validate against.",
)
def cli(xml_file, schematron_path):
    xml = xml_file.read()

    table = PrettyTable()
    table.align = "l"
    os.environ["LESS"] = "-S"

    if schematron_path:
        _, file_extension = os.path.splitext(schematron_path)
        if file_extension == ".sch":
            click.echo("Compiling schematron to svrl...")
            with open(schematron_path) as sch:
                svrl_content = compile_schematron_to_svrl(sch.read())
                schematron_validator = SchematronValidator(svrl_content)
        else:
            click.echo("Using provided svrl file.")
            schematron_validator = SchematronValidator.from_file(schematron_path)
    else:
        schematron_validator = SchematronValidator.for_dcc()

    try:
        res = schematron_validator.validate_str(xml)
    except Exception as e:
        click.echo(f"Schematron validation failed:\n{e}")
        sys.exit(1)

    if not res.is_valid:
        table.field_names = ["", "Role", "Test", "Text", "Location"]
        error_count = 0
        warning_count = 0
        information_count = 0

        for i, error in enumerate(res.failed_assertions):
            if error.role == "error":
                error_count += 1
            elif error.role == "warning":
                warning_count += 1
            elif error.role == "information":
                information_count += 1

            table.add_row(
                [
                    i,
                    error.role,
                    error.test,
                    error.text,
                    error.location,
                ]
            )

        click.echo_via_pager(
            f"{click.style(text='ERROR:', fg='red')} Schematron validation ended with {error_count} error(s), "
            f"{warning_count} warning(s) and {information_count} information messages.\n{table.get_string()}"
        )
        sys.exit(1 if error_count > 0 else 0)

    echo_success("Schematron validation exited with no errors.")
