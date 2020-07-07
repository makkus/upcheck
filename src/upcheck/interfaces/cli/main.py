# -*- coding: utf-8 -*-
import logging
import sys
import textwrap
from typing import Dict

import asyncclick as click
from rich import box
from rich.console import Console
from upcheck.exceptions import UpcheckException, ensure_upcheck_exception
from upcheck.interfaces.cli._utlis import logzero_option


log = logging.getLogger("upcheck")
console = Console()


def pretty_print_exception(exc: Exception):
    """Pretty prints an exception to the terminal."""

    frkl_exc: UpcheckException = ensure_upcheck_exception(exc)

    cols = console.width

    msg = f"[red]Error[/red]: {frkl_exc.msg}"
    for m in msg.split("\n"):
        m = textwrap.fill(m, width=cols, subsequent_indent="       ")
        console.print(m)
    click.echo()

    output_dict: Dict[str, str] = {}
    if frkl_exc.reason:
        output_dict["Reason"] = frkl_exc.reason

    if frkl_exc.parent is not None:
        output_dict["Parent exception"] = repr(frkl_exc.parent)

    if frkl_exc.solution:
        output_dict["Solution"] = frkl_exc.solution
    if frkl_exc.references:
        if len(frkl_exc.references) == 1:
            url = frkl_exc.references[list(frkl_exc.references.keys())[0]]
            reference_string = url
        else:
            reference_string = ""
            for k, v in frkl_exc.references.items():
                reference_string = f"{reference_string}{k}: {v}\n"

            reference_string.strip()
        output_dict["References"] = reference_string

    if not output_dict:
        return

    from rich.table import Table

    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Property", style="bold")
    table.add_column("Value", style="italic")

    for k, v in output_dict.items():
        table.add_row(k, v)

    console.print(table)


def handle_exception(
    exc: Exception, exit: bool = True, exit_code: int = 1, logger=None
):
    """Generic exception handler.

    Converts exceptions to an 'UpcheckException' if necessary, then pretty prints the exception details.
    """

    if logger is None:
        logger = log

    log.debug(exc, exc_info=True)
    # click.echo("Can't create context: {}".format(e))

    if hasattr(exc, "root_exc"):

        root_exc = exc.root_exc  # type: ignore
        if isinstance(root_exc, UpcheckException):
            exc = root_exc
        else:
            exc = UpcheckException(parent=exc)
    if not isinstance(exc, UpcheckException) and not issubclass(
        exc.__class__, UpcheckException
    ):
        exc = UpcheckException(exc)

    console.line()
    pretty_print_exception(exc)

    if exit:
        sys.exit(exit_code)


def handle_exc(func, exit=True, exit_code=1):
    """Wrap click commands and handle as of yet unhandled exceptions."""

    async def func_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (Exception) as e:

            handle_exception(e, exit=exit, exit_code=exit_code)

    func_wrapper.__name__ = func.__name__
    func_wrapper.__doc__ = func.__doc__
    return func_wrapper


@click.group()
@logzero_option(default_verbosity="INFO")
@click.pass_context
def command(ctx):
    """'upcheck' lets you check websites for their status and response times and redirect the collected data to specific targets (e.g. kafka, postgres).

    You can either do one-off checks, or repeat the checks using a custom interval. For more details, issue 'upcheck check --help'.

    In addition, 'upcheck' can listen to a Kafka topic, and forward metric-result-events to a target (e.g. a postgres database). More details via 'upcheck listen --help'.

    """

    log.debug("Starting upcheck cli...")
