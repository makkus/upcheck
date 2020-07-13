# Usage

## Getting help

To get information for the `upcheck` command, use the ``--help`` flag:

{{ cli("upcheck", "--help") }}

As you can seel from this output, *upcheck* has two main sub-commands: ``check`` and ``listen``, in addition to a general maintanence sub-command (``self``). For more information on each of them, again, use the ``-help`` flag.

## sub-command: ``check``

``upcheck`` defines a check as a request to an url, which measures the response time, the response code. In addition, it can contain an optional match of the website content against a provided regular expression.

The sub-command to use to do this, is -- unimaginatively -- called ``check``:

{{ cli("upcheck", "check", "--help", max_height=250) }}

Its main configuration parameters (``CHECK_ITEM``) are the check details: the website url, and the optional regex, as well as optional result targets.

### *checks* configuration

``upcheck`` can check a single or multiple websites in one go. Checks are specified as arguments at the end of the ``upcheck`` command. Each such argument is a string that is either a:

*- path to a file*
:    This will read the file with this path. The content of the file must be a valid [YAML](https://yaml.org) list, where each item is eithr a string (indicating the url to test, or a dictionary with a mandatory ``url``  and an optional ``regex`` key. Check [the ``check`` target section](../sources_and_targets/#source-check) in the *upcheck* documentation for more details and examples.

*- url*
:    If no file with a path equalling the specified string exists, the string will be interpretes as a url. In this case a simple website check using that url will be run, without any regex checking.

### *target* configuration

You can specify one or several targets. A target is defined in a yaml file, information about available target types and their configuration can be found [here](../sources_and_targets/#targets).

An example configuration for a Postgres target looks something like:

{{ inline_file_as_codeblock('examples/postgres_target.yaml', format="yaml") }}

Targets are specified using the ``--target`` command-line option:

``` console
> upcheck check --target ~/postgres.yaml https://frkl.io
```

### other parameters

In addition to the check and target details, you can specify some check parameters:

``--repeat``
:    Whether to run ``upchecks`` in a sort of 'daemon' mode, and run checks every X seconds. If not specified, the checks will be run only once. Otherwise, they will be repeated every number of seconds specified as the value of this argument.
``--terminal``
:    Prints check results on the terminal. Enabled by default if no other terminal is specified. Useful for debugging.

### Examples

#### Check a single website

{{ cli("upcheck", "check", "https://frkl.io") }}

#### Check multiple websites

{{ cli("upcheck", "check", "https://frkl.io/blog/ssh-primer", "https://duckduckgo.com", max_height=200) }}

#### Check websites using a config file

{{ cli("upcheck", "check", "examples/multi_checks.yaml", max_height=200) }}

Where the content for``examples/multi.yaml`` is:

{{ inline_file_as_codeblock("examples/multi_checks.yaml", "yaml") }}

#### Mix and match file and url config

{{ cli("upcheck", "check", "examples/multi_checks.yaml", "https://frkl.io", max_height=200) }}

#### Check a single site, send results to Kafka

``` console
> upcheck check --target examples/kafka.yaml https://frkl.io
...
...
```

With a ``kafka.yaml`` config file like:

{{ inline_file_as_codeblock("examples/kafka_target.yaml", "yaml") }}

## sub-command: ``listen``

This sub-command connects to a Kafka topic, and listenes for messages containing check results. It can then forward those
results to one or several targets:

{{ cli("upcheck", "kafka-listen", "--help", max_height=250) }}

### *source* configuration

A source is defined in a yaml file, information about available target types and their configuration can be found [here](../sources_and_targets/#sources).

An example configuration for a Kafka source looks something like:

{{ inline_file_as_codeblock('examples/kafka_source.yaml', format="yaml") }}

The source is specified using the ``--source`` command-line option:

``` console
> upcheck kafka-listen --source ~/kafka.yaml --terminal
```

### *target* configuration

You can specify one or several targets. A target is defined in a yaml file, information about available target types and their configuration can be found [here](../sources_and_targets/#targets).

An example configuration for a Postgres target looks something like:

{{ inline_file_as_codeblock('examples/postgres_target.yaml', format="yaml") }}

Targets are specified using the ``--target`` command-line option:

``` console
> upcheck kafka-listen --source ~/kafka.yaml --target ~/postgres.yaml
```

### other parameters

In addition to the check and target details, you can specify some check parameters:

``--terminal``
:    Prints check results on the terminal. Enabled by default if no other terminal is specified. Useful for debugging.

### Examples

#### Subscribe to a Kafka topic, print messages to the terminal

```console
> upcheck kafka-listen --source ~/kafka.yaml --terminal
```

#### Subscribe to a Kafka topic, print messages on terminal and write results to a Postgres database

```console
> upcheck kafka-listen --source ~/kafka.yaml --target ~/postgres.yaml --terminal
```
