import sys

import click
from prettytable import PrettyTable

from dcclib.extraction.files import FileExtractor, Ring
from dcclib_cli.commands.output import echo_err, echo_success


@click.command("files", short_help="Extract files from a DCC XML.")
@click.argument("xml_file", metavar="XML_PATH", type=click.File(encoding="utf-8"))
@click.argument("index", metavar="INDEX", type=int, required=False)
@click.option(
    "-o",
    "--output",
    "output",
    type=click.Path(),
    help="Path to write the output to.",
)
@click.option(
    "-r",
    "--ring",
    "ring",
    type=click.Choice([ring.value for ring in Ring]),
    help="Filter files by ring.",
)
def cli(xml_file, index, output, ring):
    xml_content = xml_file.read()

    try:
        file_extractor = FileExtractor.from_str(xml_content)
        files = file_extractor.extract()
    except Exception as e:
        echo_err(f"Could not extract files: {e}")
        sys.exit(1)

    if ring:
        files = [file for file in files if file.ring.value == ring]

    # display all files if no index is given to extract
    if index is None:
        echo_success("Files were extracted and are listed in the table below.")

        table = PrettyTable()
        table.field_names = ["", "Name", "File Name", "Mime Type", "Ring"]

        for i, file in enumerate(files):
            table.add_row(
                [
                    i,
                    ", ".join([f"{name.value} ({name.lang})" for name in file.name]),
                    file.file_name,
                    file.mime_type,
                    file.ring.value,
                ]
            )

        click.echo(table)
        sys.exit(0)

    if index < 0 or index >= len(files):
        echo_err(f"Index {index} out of bounds.")
        sys.exit(1)

    file = files[index]

    if output is None or output == "-":
        click.echo(file.decode_data_base64())
    else:
        with open(output, "wb") as f:
            f.write(file.decode_data_base64())
        echo_success(f"File written to {output}")
