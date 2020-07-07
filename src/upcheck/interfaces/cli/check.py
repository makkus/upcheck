# -*- coding: utf-8 -*-
import logging
from typing import Iterable, List, Optional, Tuple

import asyncclick as click
from upcheck.interfaces.cli.main import command, console, handle_exc
from upcheck.targets import CheckTarget
from upcheck.targets.terminal import TerminalTarget
from upcheck.upcheck import Upcheck
from upcheck.url_check import UrlCheck


log = logging.getLogger("upcheck")


@command.command()
@click.argument("check_urls", nargs=-1, required=True)
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
@click.option("--parallel", "-p", help="run checks in parallel", is_flag=True)
@click.pass_context
@handle_exc
async def check(
    ctx, check_urls: Tuple[str], target: Tuple[str], parallel: bool, terminal: bool
):

    _targets: List[CheckTarget] = []

    if not target:
        terminal = True
    if terminal:
        _t = TerminalTarget()
        _targets.append(_t)
    for t in target:
        _t = CheckTarget.create_from_file(t)
        _targets.append(_t)

    url_checks: Iterable[UrlCheck] = UrlCheck.create_checks(*check_urls)

    upcheck: Optional[Upcheck] = None
    try:
        upcheck = Upcheck(url_checks=url_checks, targets=_targets, parallel=parallel)

        # connect before starting the checks, so misconfiguration
        # of targets is picked up before tests are run
        console.print("- connecting to targets")
        await upcheck.connect()
        console.print(" -> all targets connected")

        console.print("- starting checks")
        await upcheck.perform_checks()
        console.print(" -> all checks finished")

    finally:

        if upcheck is not None:
            await upcheck.disconnect()
