[![PyPI status](https://img.shields.io/pypi/status/upcheck.svg)](https://pypi.python.org/pypi/upcheck/)
[![PyPI version](https://img.shields.io/pypi/v/upcheck.svg)](https://pypi.python.org/pypi/upcheck/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/upcheck.svg)](https://pypi.python.org/pypi/upcheck/)
[![pipeline status](https://gitlab.com/makkus/upcheck/badges/develop/pipeline.svg)](https://gitlab.com/makkus/upcheck/-/commits/develop)
[![coverage report](https://gitlab.com/makkus/upcheck/badges/develop/coverage.svg)](https://gitlab.com/makkus/upcheck/-/commits/develop)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# upcheck

*Collect website availability metrics*

## Links
- [Documentation](https://makkus.gitlab.io/upcheck/)
- [Source code](https://gitlab.com/makkus/upcheck)

## Description

`upcheck` checks whether websites are up, how long they take to respond, and, optionally, whether they match a provided regex. It can also, if wanted, push those metrics to a target like a Kafka topic, or directly into a Postgres database.

## Example use-case

To show the kind of tasks *upcheck* can do, here's how you would execute checks against a website every 60 seconds and send the results to a Kafka topic. Another instance of *upcheck* listens to that topic, and writes the messages to a Postgres database.

In this example, we tell *upcheck* to use Kafka and Postgres services from [Aiven](https://aiven.io), for which there exist plugins.

In order to specify necessary details for those services, we need two (yaml) files, one for each service. Something like:

``kafka.yaml``:

``` yaml
type: kafka-aiven
topic: check_metrics
group_id: upcheck
password: 'VERY_LONG_GENERATED_TOKEN_COPIED_FROM_AIVEN_WEBSITE'
project_name: upcheck_project
service_name: kafka
```

``postgres.yaml``:

```yaml
  type: postgres-aiven
  dbname: upcheck
  password: 'VERY_LONG_GENERATED_TOKEN_COPIED_FROM_AIVEN_WEBSITE'
  project_name: upcheck_project
  service_name: postgres
```

First, we need to start our listener instance:

``` console
> upcheck kafka-listen --source kafka.yaml --target postgres.yaml --terminal
- initializing kafka client and connecting to targets...
 -> done
- listening for messages, forwarding them to targets as they arrive
   -> press 'q' to stop listening
```

*Note*: the ``--terminal`` flag tells *upcheck* to print any received messages to the terminal, which is nice for debugging

Now we need to actually produce our check events. For that, we open up a different terminal and issue something like:

``` console
> upcheck check --target kafka.yaml --repeat 60 --terminal https://frkl.io
- initializing source and connecting to targets...
 -> done
- starting checks, sending results to targets
   -> press 'q' to stop the checks

  url             https://frkl.io  
  started         2020-07-10 13:13:59.792021+02:00  
  response time   914 ms  
  response code   200  
  regex matched   n/a  
...
...
...
```

We should be able to see test results coming into our Postgres database table now.

For more information about how to run checks, and configure endpoints, please refer to the [documentation](https://makkus.gitlab.io/upcheck/docs/usage).

## Downloads

### Binaries

  - [Linux](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/linux-gnu/upcheck)
  - [Windows](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/windows/upcheck.exe) -- not tested at all
  - [Mac OS X](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/darwin/upcheck) -- not available (yet)

## Update

The binary can update itself. To do that, issue:

    upcheck self update

## ToDos

- allow table name to be configurable  
- more documentation

## Known issues

- it looks like on some systems/terminals the curser is disabled after an *upcheck* run, even after the programm is finished. If this happens, issue a ``reset`` command to get your normal terminal style back. Not sure what causes that yet. Happens to me when I 'ssh' into a machine and use *upcheck* then.
- end-to-end integration test takes a long time to establish connections to source/targets, also fails every now and then but works in subsequent runs without change. Probably multiprocessing-related, needs investigation.

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


## Running tests

```console
> make test
# or
> make coverage
```

*Notes*:

- integration tests will only run if the ``RUN_INTEGRATION_TESTS`` environment variable is set to ``true``
- some integration tests need the ``AIVEN_TOKEN`` environment variable set to a valid auth token, otherwise they will be skipped

## Update project template

This project uses [cruft](https://github.com/timothycrosley/cruft) to apply updates to [the base Python project template](https://gitlab.com/frkl/template-python-project) to this repository. Check out it's documentation for more information.

    cruft update
    # interactively approve changes, make changes if necessary
    git add *
    git commit -m "chore: updated project from template"


## Copyright & license

Please check the [LICENSE](/LICENSE) file in this repository (it's a short license!).

[Parity Public License 6.0.0](https://licensezero.com/licenses/parity)

[Copyright (c) 2020 frkl OÜ](https://frkl.io)
