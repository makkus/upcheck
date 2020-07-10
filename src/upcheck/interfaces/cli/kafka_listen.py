# -*- coding: utf-8 -*-
import logging
from typing import List, Optional, Tuple

import asyncclick as click
from upcheck.interfaces.cli.main import command, console, handle_exc
from upcheck.sources import CheckSource
from upcheck.targets import CheckTarget
from upcheck.targets.terminal import TerminalTarget
from upcheck.upcheck import Upcheck


log = logging.getLogger("upcheck")


@command.command(short_help="listen to a Kafka topic for check events")
@click.option(
    "--source",
    "-s",
    multiple=False,
    required=True,
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, readable=True, resolve_path=True
    ),
    metavar="SOURCE_CONFIG",
)
@click.option(
    "--target",
    "-t",
    help="path to a target config file (multiple targets allowed)",
    multiple=True,
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, readable=True, resolve_path=True
    ),
)
@click.option(
    "--terminal",
    "-t",
    help="display check results in terminal (always on if no other targets specified)",
    is_flag=True,
)
@click.pass_context
@handle_exc
async def kafka_listen(ctx, source: str, target: Tuple[str], terminal: bool):
    """Listen to a Kafka topic that contains data about website checks, and forward that data to one or several targets.

    Both source and target parameters are paths to files that contain information about the respective item.

    For details about the Kafka source configuration, please visit https://makkus.gitlab.io/upcheck/docs/usage/#source-details. For information on how to specify the targets, visit https://makkus.gitlab.io/upcheck/docs/usage/#target-details
    """

    _source = CheckSource.create_from_file(source)

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
        console.print("- initializing kafka client and connecting to targets...")
        await upcheck.connect()
        console.print(" -> done")

        msg = "- listening for messages"
        if target:
            msg += ", forwarding them to targets as they arrive"
        console.print(msg)
        console.print("   -> press 'q' to stop the checks")

        await upcheck.start()
        console.print(" -> all checks finished")

    finally:

        if upcheck is not None:
            await upcheck.disconnect()
