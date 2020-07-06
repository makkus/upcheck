# -*- coding: utf-8 -*-
import logging
from typing import List, Tuple

import asyncclick as click
from sortedcontainers import SortedList
from upcheck.db import CheckTarget
from upcheck.interfaces.cli.main import command, console, handle_exc
from upcheck.url_check import CheckResult, UrlChecks


log = logging.getLogger("upcheck")


@command.command()
@click.argument("check_urls", nargs=-1, required=True)
@click.option(
    "--target",
    help="path to a target config file",
    multiple=True,
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, readable=True, resolve_path=True
    ),
)
@click.pass_context
@handle_exc
async def check(ctx, check_urls: Tuple[str], target: Tuple[str]):

    targets: List[CheckTarget] = []

    for t in target:
        _t = CheckTarget.load_from_file(t)
        targets.append(_t)

    try:
        for _target in targets:
            await _target.connect()

        console.print("- starting checks")

        url_checks = UrlChecks.create_checks(*check_urls)
        results: SortedList[CheckResult] = await url_checks.perform_checks()

        console.print("- checks finished:")
        for r in results:
            console.print(r)
        console.print("- sending results to targets")

        for _target in targets:
            await _target.write(*results)

        console.print("- results sent")

    finally:
        for _target in targets:
            await _target.disconnect()
