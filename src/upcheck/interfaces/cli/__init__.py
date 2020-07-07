# -*- coding: utf-8 -*-
import asyncclick as click

import upcheck.interfaces.cli.check
import upcheck.interfaces.cli.listen
import upcheck.interfaces.cli.self
from upcheck.interfaces.cli.main import command as cli


# flake8: noqa

try:
    import uvloop

    uvloop.install()
except Exception:
    pass

click.anyio_backend = "asyncio"


if __name__ == "__main__":
    cli()
