import sys

import click

from dcclib.conversion.json_converter import JSONConverter

from .output import echo_err, echo_success


@click.group("convert", short_help="Convert DCC XML files to JSON.")
def cli():
    pass


@cli.command("to-json", short_help="Convert a DCC XML file to JSON.")
@click.argument("xml_file", metavar="XML_PATH", type=click.File(encoding="utf-8"))
@click.option(
    "-o",
    "--output",
    "output",
    type=click.Path(),
    help="Path to write the output JSON to.",
)
def to_json(xml_file, output):
    xml_content = xml_file.read()

    try:
        converter = JSONConverter.from_str(xml_content)
        json_content = converter.convert()
    except Exception as e:
        echo_err(f"Could not convert to JSON: {e}")
        sys.exit(1)

    if output is None or output == "-":
        click.echo(json_content)
    else:
        with open(output, "w", encoding="utf-8") as f:
            f.write(json_content)
        echo_success(f"JSON content written to {output}")
