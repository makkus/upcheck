[![PyPI status](https://img.shields.io/pypi/status/upcheck.svg)](https://pypi.python.org/pypi/upcheck/)
[![PyPI version](https://img.shields.io/pypi/v/upcheck.svg)](https://pypi.python.org/pypi/upcheck/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/upcheck.svg)](https://pypi.python.org/pypi/upcheck/)
[![pipeline status](https://gitlab.com/makkus/upcheck/badges/develop/pipeline.svg)](https://gitlab.com/makkus/upcheck/-/commits/develop)
[![coverage report](https://gitlab.com/makkus/upcheck/badges/develop/coverage.svg)](https://gitlab.com/makkus/upcheck/-/commits/develop)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# upcheck

*Collect website availability metrics*

## Description

`upcheck` checks whether websites are up, how long they take to response, and, optionally, whether they match a provided regex. It can also, if wanted, push those metrics to a target like a Kafka topic, or directly into a Postgres database.


## Links

- [Documentation](https://makkus.gitlab.io/upcheck/)
- [Source code](https://gitlab.com/makkus/upcheck)

## Downloads

### Binaries

  - [Linux](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/linux-gnu/upcheck)
  - [Windows](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/windows/upcheck.exe) -- not tested at all
  - [Mac OS X](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/darwin/upcheck) -- not available (yet)

## Update

The binary can update itself. To do that, issue:

    upcheck self update

## Known issues

- it looks like on some systems/terminals the curser is disabled after an *upcheck* run, even after the programm is finished. If this happens, issue a ``reset`` command to get your normal terminal style back. Not sure what causes that yet. Happens to me when I 'ssh' into a machine and use *upcheck* then.

# Development

## Requirements

- Python (version >=3.6)
- pip, virtualenv
- git
- make
- [direnv](https://direnv.net/) (optional)

## Prepare development environment

Notes:

- if using *direnv*, adjust the Python version in ``.envrc`` (should not be necessary)
- if not using *direnv*, you have to setup and activate your Python virtualenv yourself, manually, before running ``make init``

```
git clone https://gitlab.com/makkus/upcheck
cd upcheck
direnv allow   # if using direnv, otherwise activate virtualenv
make init
```

## ``make`` targets

- ``init``: init development project (install project & dev dependencies into virtualenv, as well as pre-commit git hook)
- ``binary``: create binary for project (will install *pyenv* -- check ``scripts/build-binary`` for details)
- ``flake``: run *flake8* tests
- ``mypy``: run mypy tests
- ``test``: run unit tests
- ``docs``: create static documentation pages
- ``serve-docs``: serve documentation pages (incl. auto-reload)
- ``clean``: clean build directories

For details (and other, minor targets), check the ``Makefile``.


## Update project template

This project uses [cruft](https://github.com/timothycrosley/cruft) to apply updates to [the base Python project template](https://gitlab.com/frkl/template-python-project) to this repository. Check out it's documentation for more information.

    cruft update
    # interactively approve changes, make changes if necessary
    git add *
    git commit -m "chore: updated project from template"


## Copyright & license

Please check the [LICENSE](/LICENSE) file in this repository (it's a short license!), also check out the [*freckles* license page](https://freckles.io/license) for more details.

[Parity Public License 6.0.0](https://licensezero.com/licenses/parity)

[Copyright (c) 2020 frkl OÜ](https://frkl.io)
