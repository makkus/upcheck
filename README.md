[![PyPI status](https://img.shields.io/pypi/status/upcheck.svg)](https://pypi.python.org/pypi/upcheck/)
[![PyPI version](https://img.shields.io/pypi/v/upcheck.svg)](https://pypi.python.org/pypi/upcheck/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/upcheck.svg)](https://pypi.python.org/pypi/upcheck/)
[![pipeline status](https://gitlab.com/makkus/upcheck/badges/develop/pipeline.svg)](https://gitlab.com/makkus/upcheck/-/commits/develop)
[![coverage report](https://gitlab.com/makkus/upcheck/badges/develop/coverage.svg)](https://gitlab.com/makkus/upcheck/-/commits/develop)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# upcheck

*Collect website accessability metrics*

## Links

- [Documentation](https://makkus.gitlab.io/upcheck/)
- [Source code](https://gitlab.com/makkus/upcheck)

## Downloads

To install `upcheck`, download the appropriate binary from one of the links below, and set the downloaded file to be executable (``chmod +x upcheck``):

  - [Linux](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/linux-gnu/upcheck)
  - [Windows](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/windows/upcheck.exe) -- not tested at all
  - [Mac OS X](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/darwin/upcheck) -- not available (yet)

Alternatively, use the 'curly' install script for `upcheck`:

    curl https://gitlab.com/makkus/upcheck/-/raw/develop/scripts/install/upcheck.sh | bash
    source ~/.profile

## Description

Documentation still to be done.

# Development

## Requirements

- git
- [direnv](https://direnv.net/) (optional)

## Quickstart

Notes:

- to adjust the Python version to create the development virtualenv from, edit ``.envrc``
- if not using [direnv](https://direnv.net), you have to setup and activate your Python virtualenv yourself, manually, before running ``make init``

```
> git clone https://gitlab.com/frkl/upcheck
> cd upcheck
> direnv allow   # if using direnv, otherwise activate virtualenv
> make init
```

## ``make`` targets

- ``init``: init development project (install project & dev dependencies & pre-commit hook)
- ``binary``: create binary for project (will install *pyenv* -- check ``scripts/build-binary`` for details)
- ``flake``: run *flake8* tests
- ``mypy``: run mypy tests
- ``test``: run unit tests
- ``docs``: create static documentation pages
- ``serve-docs``: serve documentation pages (incl. auto-reload)
- ``clean``: clean build directories

For details (and other, minor targets), check the ``Makefile``.

## Update project template

This project uses [cruft](https://github.com/timothycrosley/cruft) to manage the base Python project template. Check
out it's documentation for more information.

    > cruft update
    # interactively approve changes, make changes if necessary
    > git add *
    > git commit -m "chore: updated project from template"



## Copyright & license

Please check the [LICENSE](/LICENSE) file in this repository (it's a short license!), also check out the [*freckles* license page](https://freckles.io/license) for more details.

[Parity Public License 6.0.0](https://licensezero.com/licenses/parity)

[Copyright (c) 2020 frkl OÜ](https://frkl.io)
