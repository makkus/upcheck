# -*- coding: utf-8 -*-
from typing import Tuple

import asyncclick as click
from upcheck.url_check import UrlChecks


try:
    import uvloop

    uvloop.install()
except Exception:
    pass

click.anyio_backend = "asyncio"


@click.group()
@click.pass_context
def cli(ctx):

    pass


@cli.command()
@click.argument("check_urls", nargs=-1, required=True)
@click.pass_context
async def check(ctx, check_urls: Tuple[str]):

    url_checks = UrlChecks.create_checks(*check_urls)

    results = await url_checks.perform_checks()

    for r in results:
        print(r)


if __name__ == "__main__":
    cli()
