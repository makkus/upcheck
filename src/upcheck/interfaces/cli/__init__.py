# -*- coding: utf-8 -*-
import asyncclick as click

import upcheck.interfaces.cli.check
import upcheck.interfaces.cli.kafka_listen
import upcheck.interfaces.cli.aiven

try:
    import frtls
    import upcheck.interfaces.cli.self
except:
    pass

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
