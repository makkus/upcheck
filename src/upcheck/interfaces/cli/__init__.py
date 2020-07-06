# -*- coding: utf-8 -*-
import asyncclick as click

# flake8: noqa

try:
    import uvloop

    uvloop.install()
except Exception:
    pass

click.anyio_backend = "asyncio"

from upcheck.interfaces.cli.main import command as cli
import upcheck.interfaces.cli.check
import upcheck.interfaces.cli.self


if __name__ == "__main__":
    cli()
