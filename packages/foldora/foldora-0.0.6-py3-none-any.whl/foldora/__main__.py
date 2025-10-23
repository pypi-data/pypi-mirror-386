import click

from foldora.commands import (
    fix_spaces,
    list_all,
    new_dirs,
    new_files,
    purge_all,
    view_contents,
)


@click.group()
@click.version_option("0.0.6")
def cli():
    """
    Foldora - File & Directory Manager CLI Tool.

    A command line utility (CLI) for file and directory operations.
    Provides commands to list, create, and purge directories and files, and more.
    """
    pass


cli.add_command(list_all, "la")
cli.add_command(new_dirs, "nd")
cli.add_command(new_files, "nf")
cli.add_command(purge_all, "pg")
cli.add_command(fix_spaces, "fs")
cli.add_command(view_contents, "vc")
