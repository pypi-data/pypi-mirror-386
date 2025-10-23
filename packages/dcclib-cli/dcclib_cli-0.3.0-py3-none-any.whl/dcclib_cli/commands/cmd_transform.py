import os.path
import sys

import click

from dcclib.transformation import XsltProcessor

from .output import echo_err, echo_success


@click.group("transform", short_help="Transform an XML file with stylesheets.")
def cli():
    pass


@cli.command("xslt", short_help="Transform an XML file with an XSLT file.")
@click.argument("xml_file", metavar="XML_PATH", type=click.File(encoding="utf-8"))
@click.argument("xslt_file", metavar="XSLT_PATH", type=click.File(encoding="utf-8"))
@click.option("-o", "--output", "output", type=click.Path(), help="Path to write the output to.")
def transform_xslt(xml_file, xslt_file, output):
    xml_content = xml_file.read()
    xslt_content = xslt_file.read()
    xslt_processor = XsltProcessor(xslt_content, os.path.dirname(xslt_file.name))

    try:
        result = xslt_processor.transform_str(xml_content)
    except Exception as e:
        echo_err(f"Transformation failed:\n{e}")
        sys.exit(1)

    if output is None or output == "-":
        click.echo(result)
    else:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
        echo_success(f"Transformation exited without errors, wrote output to {output}")
