import click
from .db import db
from .run import run

@click.group()
def cli():
    """Command line interface for xelbot."""
    pass

cli.add_command(db)
cli.add_command(run)
