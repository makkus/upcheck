# -*- coding: utf-8 -*-
import os

import asyncclick as click

import upcheck.interfaces.cli.check
import upcheck.interfaces.cli.kafka_listen
from upcheck.interfaces.cli.main import command as cli


if os.environ.get("DEVELOP", "false").lower() == "true":
    import upcheck.interfaces.cli.dev

try:
    import frtls
    import upcheck.interfaces.cli.self
except:
    pass


# flake8: noqa

try:
    import uvloop

    uvloop.install()
except Exception:
    pass

click.anyio_backend = "asyncio"


if __name__ == "__main__":
    cli()
