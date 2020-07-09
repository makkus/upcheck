# -*- coding: utf-8 -*-
"""'check' sub-command for upcheck."""

import logging
from typing import Iterable, List, Optional, Tuple

import asyncclick as click
from upcheck.interfaces.cli.main import command, console, handle_exc
from upcheck.models import UrlCheck
from upcheck.sources.check import ActualCheckCheckSource
from upcheck.targets import CheckTarget
from upcheck.targets.terminal import TerminalTarget
from upcheck.upcheck import Upcheck


log = logging.getLogger("upcheck")


@command.command(short_help="run checks against websites")
@click.argument(
    "check_urls", nargs=-1, required=True, metavar="CHECK_ITEM [CHECK_ITEM] ..."
)
@click.option(
    "--terminal",
    "-t",
    help="display check results in terminal (always on if no other targets specified)",
    is_flag=True,
)
@click.option(
    "--target",
    help="path to a target config file (multiple targets allowed)",
    multiple=True,
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, readable=True, resolve_path=True
    ),
)
@click.option(
    "--repeat",
    type=int,
    required=False,
    help="run checks repeatedly, with the value of this option as time between checks (in seconds)",
)
@click.pass_context
@handle_exc
async def check(
    ctx, check_urls: Tuple[str], target: Tuple[str], terminal: bool, repeat: None
):
    """Run checks against websites.

    Runs one or several website checks. A 'CHECK_ITEM' can either be a url of a website to check, or the path to a file containing a yaml list with websites to check (see https://makkus.gitlab.io/upcheck/docs/usage/#checks-configuration for details).

    You can specify one or several targets to send check results to with the '--target' option. If no target is specified, the details will be printed to the terminal. For more information on targets check out https://makkus.gitlab.io/upcheck/docs/usage/#target-details
    """

    url_checks: Iterable[UrlCheck] = UrlCheck.create_checks(*check_urls)

    _source = ActualCheckCheckSource(*url_checks, repeat=repeat, id="upcheck")

    _targets: List[CheckTarget] = []

    if not target:
        terminal = True
    if terminal:
        _t = TerminalTarget()
        _targets.append(_t)
    for t in target:
        _t = CheckTarget.create_from_file(t)
        _targets.append(_t)

    upcheck: Optional[Upcheck] = None
    try:
        upcheck = Upcheck(source=_source, targets=_targets)

        # connect before starting the checks, so misconfiguration
        # of targets is picked up before tests are run
        console.print("- initializing source and connecting to targets...")
        await upcheck.connect()
        console.print(" -> done")

        msg = "- starting checks"
        if target:
            msg += ", sending results to targets"
        console.print(msg)
        if repeat is not None and repeat > 0:
            console.print("   -> press 'q' to stop the checks")

        await upcheck.start(wait_for_keypress=True)
        console.print(" -> all checks finished")

    finally:

        if upcheck is not None:
            await upcheck.disconnect()
