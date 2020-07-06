# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import logging
import os
import platform
import stat
import sys

import asyncclick as click
import httpx
from asyncclick._bashcomplete import get_completion_script
from frtls.formats.output_formats import (
    delete_section_in_text_file,
    ensure_section_in_text_file,
)
from frtls.introspection.pkg_env import AppEnvironment
from rich import box
from rich.table import Table
from upcheck.interfaces.cli.main import command, console, handle_exception
from upcheck.utils import StringYAML


app_details = AppEnvironment()
app_name = app_details.app_name
app_dirs = app_details.get_app_dirs()

log = logging.getLogger("frtls")

DOWNLOAD_URLS = {
    "stable": {
        "Linux": f"https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/linux-gnu/{app_name}",
        "Darwin": f"https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/darwin/{app_name}",
        # "Linux": f"https://dl.frkl.io/linux-gnu/{app_name}",
        # "Darwin": f"https://dl.frkl.io/darwin/{app_name}",
    },
    "dev": {
        "Linux": f"https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/linux-gnu/{app_name}",
        "Darwin": f"https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/darwin/{app_name}",
    },
}

yaml = StringYAML()


@command.group(name="self")
@click.pass_context
def self_command(ctx):
    """manage/display details for this application."""
    pass


@self_command.command(name="info")
@click.pass_context
def info(ctx):
    """Print information about the application.
    """

    is_pyinstaller_bundle = (
        hasattr(sys, "frozen") and getattr(sys, "frozen") and hasattr(sys, "_MEIPASS")
    )
    if is_pyinstaller_bundle:
        exe = sys.executable
        exe_type = "binary"
    else:
        exe = sys.argv[0]
        exe_type = "python environment"

    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Property", style="bold")
    table.add_column("Value", style="italic")

    table.add_row("app_name", app_details.app_name)
    table.add_row("main_pkg", app_details.main_pkg)
    pkg_metadata = yaml.dump(app_details.pkg_meta)
    table.add_row("pkg_metadata", pkg_metadata)
    table.add_row("executable", os.path.realpath(exe))
    table.add_row("executable_type", exe_type)

    if app_dirs:
        table.add_row("config_dir", app_dirs.user_config_dir)
        table.add_row("share_dir", app_dirs.user_data_dir)
        table.add_row("cache_dir", app_dirs.user_cache_dir)

    console.print(table)


@self_command.command()
@click.option(
    "--all",
    "-a",
    help="display version information for all (frkl-) project dependencies",
    is_flag=True,
)
@click.pass_context
def version(ctx, all):
    """
    Display application version information.
    """

    if all:
        data = {}
        for k in sorted(app_details.versions.keys()):
            data[k] = app_details.versions[k]
        py_vers = sys.version.strip()
        py_vers = py_vers.replace("\n", " - ")
        py_vers = py_vers.replace("[", "")
        py_vers = py_vers.replace("]", "")
        data["python"] = py_vers

        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Name")
        table.add_column("Version")

        for k, v in data.items():
            table.add_row(k, v)

        console.print(table)
        sys.exit()

    else:
        click.echo(app_details.version)


is_pyinstaller_bundle = (
    hasattr(sys, "frozen") and getattr(sys, "frozen") and hasattr(sys, "_MEIPASS")
)
# is_pyinstaller_bundle = True

if is_pyinstaller_bundle:

    @self_command.command(name="update")
    @click.option(
        "--dev",
        help="download latest development version instead of stable",
        is_flag=True,
    )
    def update(dev):
        """
        Update the application binary.
        """

        if not is_pyinstaller_bundle:
            click.echo()
            click.echo(
                f"The running executable is not the packaged '{app_name}' binary, updated not supported."
            )
            click.echo()
            sys.exit(1)

        # path = os.path.realpath(sys.argv[0])
        path = os.path.realpath(sys.executable)
        # print("exe: {}".format(path))
        # path = os.path.realpath("/home/markus/.local/share/freckles/bin/frecklecute")

        if not path.endswith(os.path.sep + app_name):
            click.echo()
            click.echo(
                f"Can't update, not a supported binary name (must be '{app_name}'): {os.path.basename(path)}"
            )
            click.echo()
            sys.exit()

        if not dev:
            version = "stable"
        else:
            version = "dev"

        pf = platform.system()
        url = DOWNLOAD_URLS[version].get(pf, None)
        if url is None:
            click.echo()
            click.echo("Can't update, platform '{}' not supported.".format(pf))
            click.echo()
            sys.exit(1)

        click.echo()
        click.echo("downloading: {}".format(url))

        temp_path = path + ".tmp"
        with open(temp_path, "wb") as f:

            try:
                r = httpx.get(url, allow_redirects=True)
                f.write(r.content)
            except (Exception) as e:
                click.echo("   -> download error: {}".format(e))
                click.echo()
                sys.exit(1)
            # finally:
            #     cursor.show()

        orig_path = path + ".orig"
        try:
            st = os.stat(temp_path)
            os.chmod(temp_path, st.st_mode | stat.S_IEXEC)
            click.echo(f"updating {app_name} binary: {app_name}".format(path))
            os.rename(path, orig_path)
            os.rename(temp_path, path)
        except Exception() as e:
            handle_exception(e)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if not os.path.exists(path) and os.path.exists(orig_path):
                os.rename(orig_path, path)
            if os.path.exists(orig_path):
                os.unlink(orig_path)

        click.echo()


@self_command.command(name="shell-completion")
@click.argument("shell", required=False, nargs=1, type=click.Choice(["bash", "zsh"]))
@click.option(
    "--add-to-rc",
    help="add shell completion code to shell rc file",
    is_flag=True,
    default=False,
)
@click.option(
    "--remove-from-rc",
    help="remove shell completion code from shell rc file",
    is_flag=True,
    default=False,
)
@click.option(
    "--rc-file", "-f", help="file to add the completion code to", required=False
)
@click.option(
    "--backup/--no-backup",
    help="whether to create a backup of the rc file",
    required=False,
    default=True,
    show_default=True,
)
@click.pass_context
async def shell_completion(ctx, shell, add_to_rc, remove_from_rc, rc_file, backup):

    if add_to_rc and remove_from_rc:
        click.echo(
            "Can't both add and remove the shell completion code from rc file. Doing nothing..."
        )
        sys.exit(1)

    if not shell:
        shell = os.path.basename(os.environ.get("SHELL"))

    if not shell:
        click.echo("Can't autodetect shell, please set manually.")
        sys.exit(1)

    prog_name = os.path.basename(sys.argv[0])
    complete_var = "_%s_COMPLETE" % (prog_name.replace("-", "_")).upper()

    script = get_completion_script(prog_name, complete_var, shell)

    if not add_to_rc and not remove_from_rc:
        click.echo(script)
        sys.exit()

    if not rc_file:
        if shell == "zsh":
            rc_file = os.path.expanduser("~/.zshrc")
        elif shell == "bash":
            rc_file = os.path.expanduser("~/.bashrc")

    comment_line = "# -----------------------------------------------------------"
    start_section = f"# START auto-created shell completion function for {prog_name}"
    end_section = f"# END auto-created shell completion function for {prog_name}"

    if add_to_rc:
        ensure_section_in_text_file(
            path=rc_file,
            section_content=script,
            prefix=[comment_line, start_section],
            postfix=[end_section, comment_line],
        )
    elif remove_from_rc:
        delete_section_in_text_file(
            path=rc_file,
            prefix=[comment_line, start_section],
            postfix=[end_section, comment_line],
        )

    # pattern = re.compile(f"{comment_line}(?:\n|\r|\r\n?){start_section}[\s\S]*{end_section}(?:\n|\r|\r\n?){comment_line}", re.MULTILINE)
    # result = re.search(pattern, content)
