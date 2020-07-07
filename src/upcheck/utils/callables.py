# -*- coding: utf-8 -*-
import atexit
import logging
import os
import sys
from typing import Any, Dict, Mapping, Optional, Union

from anyio import create_task_group, run_in_thread
from rich.console import Console


log = logging.getLogger("frtls")

DEFAULT_STOP_KEY = "q"
DEFAULT_MESSAGE = "Press '{}' to exit."


async def wait_for_tasks(*tasks: Mapping[str, Any], cancel_task: Dict = None):

    async with create_task_group() as tg:
        for task in tasks:
            func = task["func"]
            args = task.get("args", [])
            await tg.spawn(func, *args)

        if cancel_task:

            async def wrap():
                func = cancel_task["func"]
                args = cancel_task.get("args", [])
                await func(*args)
                await tg.cancel_scope.cancel()

            await tg.spawn(wrap)


async def wait_for_tasks_or_user_keypress(
    *tasks: Mapping[str, Any],
    stop_key=DEFAULT_STOP_KEY,
    msg: Union[str, bool] = False,
    console: Optional[Console] = None
):

    cancel_task = {"func": wait_for_user_input, "args": [stop_key, msg, console]}
    await wait_for_tasks(*tasks, cancel_task=cancel_task)


async def wait_for_user_input(
    stop_key=DEFAULT_STOP_KEY,
    msg: Union[str, bool] = False,
    console: Optional[Console] = None,
):

    if msg:
        if msg is True:
            msg = DEFAULT_MESSAGE.format(stop_key)

    def wrap():

        if msg:
            print(msg)
        c = None

        if console is not None:
            console.show_cursor(show=False)

        def show_cursor():
            if console is not None:
                console.show_cursor(show=True)

        atexit.register(show_cursor)

        try:
            while c != stop_key:
                c = wait_for_keypress()
        except KeyboardInterrupt:
            print("Execution interrupted by user, exiting...")
        finally:
            show_cursor()

    log.debug("Waiting for user input...")
    await run_in_thread(wrap)
    log.debug("Waiting finished...")


def wait_for_keypress() -> str:

    pressed_key: str = ""
    if os.name == "nt":
        import msvcrt  # type: ignore

        pressed_key = msvcrt.getch()  # type: ignore
    else:
        import termios  # type: ignore

        fd = sys.stdin.fileno()

        last = termios.tcgetattr(fd)
        next = termios.tcgetattr(fd)
        next[3] = next[3] & ~termios.ICANON & ~termios.ECHO  # type: ignore
        termios.tcsetattr(fd, termios.TCSANOW, next)

        try:
            pressed_key = sys.stdin.read(1)
        except IOError:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, last)

    return pressed_key
