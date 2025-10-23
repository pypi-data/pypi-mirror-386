import click


def echo_err(msg: str):
    click.echo(f"{click.style('ERROR:', fg='red')} {msg}", err=True)


def echo_warn(msg: str):
    click.echo(f"{click.style('WARNING:', fg='yellow')} {msg}", err=True)


def echo_info(msg: str):
    click.echo(f"{click.style('INFO:', fg='blue')} {msg}", err=True)


def echo_success(msg: str):
    click.echo(f"{click.style('SUCCESS:', fg='green')} {msg}")
