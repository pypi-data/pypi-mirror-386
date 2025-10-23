import os
import sys

import click
from prettytable import PrettyTable

from dcclib.validation import (
    SchemaVersion,
    XsdValidator,
)
from dcclib_cli.commands.output import echo_err, echo_success

SCHEMA_VERSIONS = [version.name.replace("_", ".") for version in SchemaVersion]


@click.command(
    "xsd",
    short_help="Validate an DCC XML file against the DCC schema.",
)
@click.argument("xml_file", metavar="XML_PATH", type=click.File(encoding="utf-8"))
@click.option(
    "-r",
    "--release",
    default="latest",
    type=click.Choice(SCHEMA_VERSIONS + ["latest"]),
    help="Release version of the schema to validate against.",
)
@click.option(
    "-s",
    "--schema",
    "schema_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Path to the schema file to validate against.",
)
def cli(xml_file, release, schema_path):
    xml = xml_file.read()

    table = PrettyTable()
    table.align = "l"
    os.environ["LESS"] = "-S"

    # use schema path if provided, otherwise use schema version
    if schema_path:
        xsd_validator = XsdValidator.from_file(schema_path)
    else:
        # click checks that the release is in SCHEMA_VERSIONS
        version = SchemaVersion[release.replace(".", "_")]
        xsd_validator = XsdValidator.from_version(version)

    try:
        res = xsd_validator.validate_str(xml)
    except Exception as e:
        echo_err(f"XSD validation failed:\n{e}")
        sys.exit(1)

    if not res.is_valid:
        table.field_names = [
            "",
            "Column",
            "Domain",
            "Domain Name",
            "Level",
            "Level Name",
            "Line",
            "Message",
            "Type",
            "Type Name",
        ]

        for i, error in enumerate(res.errors):
            table.add_row(
                [
                    i,
                    error.column,
                    error.domain,
                    error.domain_name,
                    error.level,
                    error.level_name,
                    error.line,
                    error.message,
                    error.type,
                    error.type_name,
                ]
            )

        click.echo_via_pager(f"{click.style(text='ERROR:', fg='red')} XSD validation failed.\n{table.get_string()}")
        sys.exit(1)

    echo_success("XSD validation exited with no errors.")
