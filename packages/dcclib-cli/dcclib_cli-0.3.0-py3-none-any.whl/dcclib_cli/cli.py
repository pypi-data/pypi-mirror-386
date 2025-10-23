import importlib.metadata

import click

from dcclib_cli.commands import (
    convert,
    extract,
    signature,
    transform,
    validate,
)

COMMANDS = {cmd.name: cmd for cmd in [extract, validate, transform, signature, convert]}
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class DccCLI(click.Group):
    def list_commands(self, ctx):
        return sorted(COMMANDS.keys())

    def get_command(self, ctx, name):
        if name not in COMMANDS:
            return None
        return COMMANDS[name]


@click.command(cls=DccCLI, context_settings=CONTEXT_SETTINGS)
@click.version_option(importlib.metadata.version("dcclib"), "--version", "-v")
def cli():
    pass


def main():  # pragma: no cover
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()
