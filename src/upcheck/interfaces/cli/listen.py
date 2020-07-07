# -*- coding: utf-8 -*-
import logging
from typing import List, Tuple

import asyncclick as click
from upcheck.interfaces.cli.main import command, console, handle_exc
from upcheck.sources import CheckSource
from upcheck.targets import CheckTarget
from upcheck.targets.terminal import TerminalTarget


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
async def listen(ctx, source: str, target: Tuple[str], terminal: bool):
    """Listen to a Kafka topic that contains data about website checks, and forward that data to one or several targets.


    """

    targets: List[CheckTarget] = []
    if not target:
        terminal = True

    if terminal:
        _t = TerminalTarget()
        targets.append(_t)

    for t in target:
        _t = CheckTarget.create_from_file(t)
        targets.append(_t)

    check_source = CheckSource.create_from_file(source)

    try:

        console.print("- connecting to metric source...")
        await check_source.connect()
        console.print("  -> connected")

        console.print(
            f"- starting to listen for check metrics from '{check_source.get_id()}'..."
        )
        console.print("  -> press 'q' to stop")
        await check_source.start(*targets)
        console.print("  -> listener stopped")
    finally:
        if check_source is not None:
            await check_source.disconnect()
