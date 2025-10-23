import sys
from decimal import Decimal, InvalidOperation

import click

from dcclib.extraction.formulae import FormulaExtractor
from dcclib_cli.commands.output import echo_err


class KeyDecimalParamType(click.ParamType):
    """
    Custom parameter type for key=decimal_value,decimal_value,... pairs.
    """

    name = "key=decimal_value,decimal_value,..."

    def convert(self, value, param, ctx):
        try:
            key, value = value.split("=")
            return key, Decimal(value) if "," not in value else [Decimal(val) for val in value.split(",")]
        except (ValueError, InvalidOperation):
            self.fail(
                f"{value} is not a valid key=decimal_value,decimal_value,... pair.",
                param,
                ctx,
            )


def print_formula(formula):
    """
    Print a formula and its variables.
    @param formula: the formula to print
    """
    click.echo()
    click.echo(formula.expression)
    click.echo()
    click.echo(f"Variables: {', '.join(formula.variables)}")
    click.echo(f"Bound variables: {', '.join(formula.bound_variables)}")
    click.echo()
    click.echo("Variables from DCC XML:")
    for key, value in formula.variables.items():
        value_str = ", ".join(str(val) for val in value) if isinstance(value, list) else str(value)
        click.echo(f"{key} = {value_str}")

    click.echo()


@click.command("formulae", short_help="Evaluate a formula from an XML file.")
@click.argument("xml_file", metavar="XML_PATH", type=click.File(encoding="utf-8"))
@click.option(
    "-v",
    "--variable",
    "variable",
    type=KeyDecimalParamType(),
    multiple=True,
    help="Specify variables in the form of key=decimal_value.",
)
def cli(xml_file, variable):
    xml_content = xml_file.read()
    extractor = FormulaExtractor.from_str(xml_content)
    formulae = extractor.extract()

    if not formulae:
        echo_err("No formulae found.")
        return

    for key, value in variable:
        value_str = ", ".join(str(val) for val in value) if isinstance(value, list) else str(value)
        click.echo(f"Variable: {key} = {value_str}")

    evaluation_failed = False
    for formula in formulae:
        print_formula(formula)

        try:
            result = formula.evaluate(dict(variable))
        except Exception as e:
            echo_err(f"Could not evaluate formula: {e}")
            evaluation_failed = True
            continue

        click.echo("Results:")
        for res in result:
            click.echo(res)
        click.echo()

    if evaluation_failed:
        sys.exit(1)
