# Usage

## Getting help

To get information for the `upcheck` command, use the ``--help`` flag:

{{ cli("upcheck", "--help") }}

As you can seel from this output, *upcheck* has two main sub-commands: ``check`` and ``listen``, in addition to a general maintanence sub-command (``self``). For more information on each of them, again, use the ``-help`` flag.

## sub-command: ``check``

``upcheck`` defines a check as a request to an url, which measures the response time, the response code. In addition, it can contain an optional match of the website content against a provided regular expression.

The sub-command to use to do this, is -- unimaginatively -- called ``check``:

{{ cli("upcheck", "check", "--help") }}

Its main configuration parameters (``CHECK_ITEM``) are the check details: the website url, and the optional regex, as well as optional result targets.

### *checks* configuration

``upcheck`` can check a single or multiple websites in one go. Checks are specified as arguments at the end of the ``upcheck`` command. Each such argument is a string that is either a:

*- path to a file*
:    This will read the file with this path. The content of the file must be a valid [YAML](https://yaml.org) list, where each item is eithr a string (indicating the url to test, or a dictionary with a mandatory ``url``  and an optional ``regex`` key. Check the [target section](/docs/usage/#target-details) for more details and examples.

*- url*
:    If no file with a path equalling the specified string exists, the string will be interpretes as a url. In this case a simple website check using that url will be run, without any regex checking.


#### Target details

#### Other parameters

In addition to the check and target details, you can specify some check parameters:

``--repeat``
:    Whether to run ``upchecks`` in a sort of 'daemon' mode, and run checks every X seconds. If not specified, the checks will be run only once. Otherwise, they will be repeated every number of seconds specified as the value of this argument.
``--paralell``
:    Whether to run the checks in parallel. This should be ok for a small number of sites to check, but might skew your response time results in case you run hundreds of checks.

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

asdf

### Source details
