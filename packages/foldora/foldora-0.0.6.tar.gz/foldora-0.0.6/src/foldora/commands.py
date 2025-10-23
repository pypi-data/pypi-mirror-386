import os
from operator import indexOf
from pathlib import Path
from typing import Union

import click

from foldora.utils import dir_count, file_count, sub_del


# Colored messages
def color_handler(string: str, fg_color: Union[str, None] = None):
    click.echo(click.style(string, fg=fg_color), color=True)


@click.command(help="List all files and directories.")
@click.argument("paths", nargs=-1, type=click.Path(exists=True, file_okay=False, readable=True, path_type=Path))
@click.option("-f", "--files", is_flag=True, help="List only files.")
@click.option("-d", "--dirs", is_flag=True, help="List only directories.")
def list_all(paths, dirs, files):
    """
    List files and directories in the specified paths.

    This function lists the files and directories within one or more specified paths.
    If no paths are provided, it defaults to the current working directory. The function
    can be filtered to list only files or only directories based on the given options.

    Arguments:
        paths (tuple of str, optional):
            One or more directory paths to list. If not provided, the current directory is used.
        --files (optional):
            If specified, only files will be listed.
        --dirs (optional):
            If specified, only directories will be listed.

    Examples:
        - fd la
        - fd la --files
        - fd la --dirs
        - fd la --files /path/to/directory
        - fd la --dirs /path/to/directory
        - fd la --files /path1 /path2
        - fd la --dirs /path1 /path2

    Notes:
        - If a specified path is a file, only that file will be listed.
        - Hidden files and directories may be included, depending on the system settings.
        - Multiple paths can be provided to list contents from different directories simultaneously.
    """

    # Empty path option
    if len(paths) == 0:
        normalized_path = Path().cwd().resolve()
        sorted_entries = sorted(normalized_path.iterdir(), key=lambda en: en.name.lower())

        file_type = file_count(normalized_path)
        dir_type = dir_count(normalized_path)

        click.echo("\t")

        if dirs:
            color_handler(f"# {normalized_path} \t ({dir_type}) #")

            if dir_type == 0:
                color_handler("NONE", "red")
                click.echo("\t")
                return

            for entry in sorted_entries:
                if entry.is_dir():
                    color_handler(f"> {'[DIR]':<8}pos : {indexOf(sorted_entries, entry):<8}{entry.name}", "green")
                continue

        if files:
            color_handler(f"# {normalized_path} \t ({file_type}) #")

            if file_type == 0:
                color_handler("NONE", "red")
                click.echo("\t")
                return

            for entry in sorted_entries:
                if entry.is_file():
                    color_handler(f"> {'[FILE]':<8}pos : {indexOf(sorted_entries, entry):<8}{entry.name}", "blue")
                continue

        if not files and not dirs:
            color_handler(f"# {normalized_path} \t (D:{dir_type} | F:{file_type}) #")

            if len(list(normalized_path.iterdir())) == 0:
                color_handler("NONE", "red")
                click.echo("\t")
                return

            for entry in sorted_entries:
                if entry.is_dir():
                    color_handler(f"> {'[DIR]':<8}pos : {indexOf(sorted_entries, entry):<8}{entry.name}", "green")

            for entry in sorted_entries:
                if entry.is_file():
                    color_handler(f"> {'[FILE]':<8}pos : {indexOf(sorted_entries, entry):<8}{entry.name}", "blue")

        click.echo("\t")
        return

    # At least one given path
    for i, path in enumerate(paths):
        normalized_path = Path(path).resolve()
        entries = sorted(normalized_path.iterdir(), key=lambda en: en.name.lower())

        file_type = file_count(normalized_path)
        dir_type = dir_count(normalized_path)

        click.echo("\t")

        if not entries:
            color_handler(f"# {normalized_path} \t ({len(entries)}) #")
            color_handler("NONE", "red")
            continue

        if files:
            color_handler(f"# {normalized_path} \t ({file_type}) #")

            if file_type == 0:
                color_handler("None", "red")
            for entry in entries:
                if entry.is_file():
                    color_handler(f"> {'[FILE]':<8}pos : {indexOf(entries, entry):<8}{entry.name}", "blue")
            continue

        if dirs:
            color_handler(f"# {normalized_path} \t ({dir_type}) #")

            if dir_type == 0:
                color_handler("None", "red")
            for entry in entries:
                if entry.is_dir():
                    color_handler(f"> {'[DIR]':<8}pos : {indexOf(entries, entry):<8}{entry.name}", "green")
            continue

        if not files and not dirs:
            color_handler(f"# {normalized_path} \t (D:{dir_type} | F:{file_type}) #")

            for entry in entries:
                if entry.is_dir():
                    color_handler(f"> {'[DIR]':<8}pos : {indexOf(entries, entry):<8}{entry.name}", "green")

            for entry in entries:
                if entry.is_file():
                    color_handler(f"> {'[FILE]':<8}pos : {indexOf(entries, entry):<8}{entry.name}", "blue")

    click.echo("\t")


@click.command(help="Create one or more directories.")
@click.argument("paths", nargs=-1, type=click.Path(file_okay=False, exists=False, path_type=Path))
def new_dirs(paths):
    """
    Create one or more directories.

    Creates one or more directories. If a parent directory in the specified path does not exist, it will be created automatically. Existing directories are not modified.

    Arguments:
        paths (tuple of str):
            Paths to the directories to be created.

    Examples:
        fd nd directory1 directory2
        fd nd /path/to/parent/new_directory

    Notes:
        - Does not modify existing directories.
        - Supports creating multiple directories in a single command.
        - Creates all necessary parent directories if they do not exist.
    """

    if len(paths) < 1:
        color_handler("\n> A Path is Required\n", "yellow")
        return

    click.echo("\t")

    for i, p in enumerate(paths):
        try:
            if Path(p).exists():
                color_handler("> Path already exists", "yellow")
                continue

            p.mkdir(parents=True, exist_ok=True)
            color_handler(f"> {paths[i]} DIR CREATED", "green")
        except PermissionError:
            color_handler(f"> Permission Denied\n", "red")
            return

    click.echo("\t")


@click.command(help="Create one or more files.")
@click.argument("paths", nargs=-1, type=click.File(mode="w", encoding="utf-8"))
@click.option(
    "-tp",
    "--to-path",
    nargs=1,
    type=click.Path(exists=False, path_type=Path),
    help="Custom path where the file(s) will be added.",
)
def new_files(paths, to_path):
    """
    Create one or more files in the current or specified directory.

    Creates one or more empty files in the current directory or a specified path. If a custom path is provided, the files are created in that location instead.

    Arguments:
        filenames (tuple of str):
            Names of the files to be created.
        to_path (str, optional):
            Custom directory where the files should be created. If not provided, the current directory is used.

    Examples:
        fd nf file1.txt file2.txt
        fd nf -tp /path/to/dir file1.txt file2.txt

    Notes:
        - Supports creating multiple files in a single command.
        - Existing files with the same names will not be overwritten.
        - If the specified directory does not exist, an error will be raised.
    """

    click.echo("\t")

    if to_path:
        try:
            if not to_path.exists():
                to_path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            color_handler(f"> Permission Denied", "red")
            click.echo("\t")
            return

        for f in paths:
            try:
                with open(to_path / f.name, "w") as file:
                    file.write("")

                color_handler(f"> {f.name} FILE CREATED.", "green")
            except PermissionError:
                color_handler("> Permission Denied", "red")
                click.echo("\t")
                return

        click.echo("\t")
        return

    if len(paths) == 0:
        color_handler("> A Path is Required!\n", "yellow")
        return

    for f in paths:
        try:
            if not Path(f.name).parent.exists():
                Path(f.name).parent.mkdir(parents=True, exist_ok=True)

            with open(f.name, "w") as file:
                file.write("")

            color_handler(f"> {f.name} FILE CREATED.", "blue")
        except PermissionError:
            color_handler("> Permission Denied", "red")
            click.echo("\t")
            return

    click.echo("\t")


@click.command(help="Delete specified files and directories permanently.")
@click.argument(
    "paths",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, readable=True, path_type=Path),
)
def purge_all(paths):
    """
    Delete specified files and directories.

    Permanently deletes the specified files and directories. Requires user confirmation before proceeding to prevent accidental data loss. Useful for quickly removing unwanted files or entire directories.

    Arguments:
        paths (tuple of Path):
            One or more file or directory paths to be deleted.

    Examples:
        fd pg file1 directory1

    Notes:
        - Use with caution, as this action cannot be undone.
        - Directories will be deleted recursively, including all their contents.
        - Ensure you have the necessary permissions to delete the specified paths.
    """

    dirs = []
    files = []
    click.echo("\t")

    if len(paths) < 1:
        color_handler("> A Path is Required!", "yellow")
        click.echo("\t")
        return

    if not click.confirm(text="Proceed with deleting?", abort=True):
        return

    click.echo("\t")

    for i, path in enumerate(paths):

        # Directories
        if path.is_dir():
            try:
                sub_del(path)
                dirs.append(i)
            except PermissionError:
                color_handler(f"> Permission Denied", "red")
                click.echo("\t")
                return

        # Files
        if path.is_file():
            try:
                path.unlink(path)
                files.append(i)
            except PermissionError:
                color_handler(f"> Permission Denied", "red")
                click.echo("\t")
                return

    if len(dirs) > 0:
        color_handler(f"> ({len(dirs)}) DIR(s) REMOVED.", "green")

    if len(files) > 0:
        color_handler(f"> ({len(files)}) FILE(s) REMOVED.", "blue")

    click.echo("\t")


@click.command(help="Display the contents of one or more files.")
@click.argument("files", nargs=-1, type=click.File(mode="r"))
def view_contents(files):
    """
    Display the contents of one or more files.

    Prints the contents of one or more specified files to the console. Each file is read in order,and its contents are displayed sequentially. Useful for quickly reviewing file contents from the command line.

    Arguments:
        files (tuple of File):
            One or more file objects whose contents should be displayed.

    Examples:
        fd vc file1.txt file2.txt

    Notes:
        - Files must be readable, or an error will be raised.
        - Supports multiple files, displaying each file's content in sequence.
    """

    click.echo("\t")

    if len(files) < 1:
        color_handler("> A Path is Required!", "yellow")
        click.echo("\t")
        return

    for file in files:
        color_handler(f"============[{file.name}]============", "green")
        click.echo("\t")
        click.echo(f"{file.read().strip()}", nl=True)

        if file != files[-1]:
            click.echo("\t")

    click.echo("\t")


@click.command(help="Replace spaces in file and folder names with underscores.")
@click.argument(
    "path",
    nargs=1,
    required=False,
    type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True, path_type=Path),
)
def fix_spaces(path: Path):
    """
    Replace spaces in file and folder names with underscores.

    This command renames files and folders by replacing any spaces in their names with underscores. It operates on the specified directory (or the current directory if none is provided). All files and directories in that location will have their names updated to remove spaces.

    Arguments:
        path (str, optional):
            The directory to process. Defaults to the current working directory if not specified.

    Examples:
        fd fs /path/to/dir

    Notes:
        - By default, only top-level files and folders are renamed.
    """

    click.echo("\t")

    if not path:
        path = "."

    for df in os.listdir(path):
        origin_path: Path = Path(f"{path}/{df}").resolve()
        contain_space = len(df.split(" "))

        try:
            if os.path.isfile(origin_path) and contain_space > 1:
                os.rename(origin_path, f"{path}/{df.replace(' ', '_')}")
                color_handler(f"> DONE{'':<5}{df}", "green")

            if os.path.isdir(origin_path) and contain_space > 1:
                os.rename(origin_path, f"{path}/{df.replace(' ', '_')}")
                color_handler(f"> DONE{'':<5}{df}", "green")

            continue
        except PermissionError:
            color_handler("> Permission Denied", "red")
            return

    click.echo("\t")
