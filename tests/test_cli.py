# -*- coding: utf-8 -*-
import os

import pytest
from asyncclick.testing import CliRunner
from upcheck.interfaces.cli import main


os.environ["UPCHECK_NO_WAIT"] = "true"


@pytest.mark.anyio
async def test_cli_help():

    runner = CliRunner()
    result = await runner.invoke(main.command)
    assert result.exit_code == 0
    assert "'upcheck' lets you check websites" in result.output

    result = await runner.invoke(main.command, ["--help"])
    assert result.exit_code == 0
    assert "'upcheck' lets you check websites" in result.output

    result = await runner.invoke(main.command, ["check", "--help"])
    assert result.exit_code == 0
    assert "Run checks against websites" in result.output

    result = await runner.invoke(main.command, ["kafka-listen", "--help"])
    assert result.exit_code == 0
    assert "Listen to a Kafka topic" in result.output


@pytest.mark.anyio
async def test_simple_website_check(httpserver):

    httpserver.expect_request("/abc").respond_with_data("abcdefghijklmnopqrstuvwxyz")
    check_url = f"http://{httpserver.host}:{httpserver.port}/abc"

    runner = CliRunner()
    result = await runner.invoke(main.command, ["check", "--terminal", check_url])

    assert result.exit_code == 0
    # TODO: there seems to be an issue where the CliRunner does not pick up on
    # output that is created by rich.console.print(xxx), needs investigation...
    # assert check_url in result.output
    # assert "response_code" in result.output
    # assert "200" in result.output
