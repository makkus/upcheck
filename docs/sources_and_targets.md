# Sources & Targets

*upcheck* works by using components called *sources* and *targets*. A *source* is a component that emits check metrics, and
a *target* is a component that -- who would have guessed? -- receives those. An *upcheck* run consists of a single *source* component, and one or several *targets*.

## Sources

Sources emit check result data. Usually, this will be done directly after a check. In some cases you might want to use Kafka as an intermediate data streaming component, in which case you would use one of the '*kafka-*' sources below.

### source: ``check``

This is the default source and a special case at the same time, as it is the module that actually checks websites and gathers the results from those checks. This check is used when running the ``upcheck check`` subcommand, and it's configuration format is different than for other sources.

To use a *check* configuration, just use it as an argument to the ``upcheck check`` subcommand, something like:

```console
> upcheck check /home/markus/website_checks.yaml
```

#### Configuration

The main way to configure checks for *upchecks* is via YAML files. A single check consists of a required url and an optional regex pattern, so in the normal case your checks configuration file contains a YAML list with dictionaries as items, like:

``` yaml
- url: [url_1]
  regex: [regex_1]
- url: [url_2]
- url: [url_3]
  regex: [regex_3]
```

If no regex is required, the list item can also be a simple string (indicating the url):

```yaml
- url_1
- url_2
- url: [url_3]
  repgex: [regex_3]
- url_4
```  

#### Example configs

Here are a few examples of 'real-life' check configuration yaml files:

##### Single url, no regex

{{ inline_file_as_codeblock('examples/single_item_check.yaml', format="yaml") }}

##### Single url, regex

{{ inline_file_as_codeblock('examples/single_item_with_regex.yaml', format="yaml") }}

##### Multiple urls, mixed style (string and dict)

{{ inline_file_as_codeblock('examples/multi_checks.yaml', format="yaml") }}

### source: ``kafka``

A source that listens to a Kafka topic, in order to forward the received (check-result) messages to one or several targets.

To use a *kafka* source, specify the path to your configuration YAML file in the ``kafka-listen`` subcommand:

```console
> upcheck kafka-listen --source /home/markus/kafka.yaml --target ...
```
#### Configuration

The configuration for a *kafka* source uses the following keys:

``type`` (required value: ``kafka``)
:    The source type.

``host`` (required)
:    A host that runs the Kafka service.

``port`` (required)
:    The port where the Kafka service runs on.

``topic`` (required)
:    The topic to send the check metrics to.

``cafile`` (optional)
:    The path to a CA file (for server certificate validation).

``certfile`` (optional)
:    The path to a certificate (for authentication).

``keyfile`` (optional)
:    The path to a key file (for authentication).


#### Example configs

##### Kafka target with ca verification and certificate auth

{{ inline_file_as_codeblock('examples/kafka_source.yaml', format="yaml") }}


#### source: ``kafka-aiven``

A convenience wrapper source, in case you are using [aiven](https://aiven.io) to run your Kafka service. It removes most of the configuration options, and figures most configuration values (certs, etc.) out by itself, using the Aiven REST API.

Use like:

```console
> upcheck kafka-listen --source /home/markus/kafka_aiven.yaml --target ...
```

#### Configuration

``type`` (required value: ``kafka-aiven``)
:    The source type.

``topic`` (required)
:    The topic to send messages to.

``password`` (required)
:    An authentication token for the Aiven API, or the account password if using ``email`` (below).

``email`` (optional)
:    If a value for the ``email`` is specified, *upcheck* assumes username/password authentication instead of the token-based one.

``project_name`` (optional)
:    The project name. If not specified, *upcheck* checks the list of projects, and if only one exists that one will be used. If multiple projects exist, an error will be thrown.

``service_name`` (optional)
:    The name of the Kafka service in the used project. If not specified, *upcheck* will search for Kafka services in that project, and if only one service is found, that one will be used. If multiple Kafka services exist, an error will be thrown.

#### Example configs

##### Using username and password to authencicate

{{ inline_file_as_codeblock('examples/kafka_source_aiven.yaml', format="yaml") }}

##### Using an authentication token to authencicate

{{ inline_file_as_codeblock('examples/kafka_source_aiven_token.yaml', format="yaml") }}

## Targets

Targets consume check result data. If no target is specified, the ``terminal`` target -- which only prints out the check results via stdout -- will be used as default. Other currently implemented targets are ``kafka`` (which writes result data to a Kafka topic), or ``postgres`` (which writes result data to a postgres table).

### target: ``terminal``

The default target, if no other is specified. Prints check results to stdout.

#### Configuration

No configuration necessary.

#### Example configs

n/a

### target: ```kafka```

Writes check resources to a Kafka topic.

#### Configuration

``type`` (required value: ``kafka``)
:    The source type.

``host`` (required)
:    A host that runs the Kafka service.

``port`` (required)
:    The port where the Kafka service runs on.

``topic`` (required)
:    The topic to send the check metrics to.

``group_id`` (optional)
:    The group id of the Kafka consumer.

``cafile`` (optional)
:    The path to a CA file (for server certificate validation).

``certfile`` (optional)
:    The path to a certificate (for authentication).

``keyfile`` (optional)
:    The path to a key file (for authentication).


#### Example configs

##### Kafka target with ca verification and certificate auth

{{ inline_file_as_codeblock('examples/kafka_target.yaml', format="yaml") }}

### target: ``kafka-aiven``

A convenience wrapper target, in case you are using [aiven](https://aiven.io) to run your Kafka service. It removes most of the configuration options, and figures most configuration values (certs, etc.) out by itself, using the Aiven REST API.

Use like:

```console
> upcheck check --target /home/markus/kafka_target_aiven.yaml https://frkl.io
```

``type`` (required value: ``kafka-aiven``)
:    The source type.

``topic`` (required)
:    The topic to send messages to.

``group_id`` (optional)
:    The group id of the Kafka consumer.

``password`` (required)
:    An authentication token for the Aiven API, or the account password if using ``email`` (below).

``email`` (optional)
:    If a value for the ``email`` is specified, *upcheck* assumes username/password authentication instead of the token-based one.

``project_name`` (optional)
:    The project name. If not specified, *upcheck* checks the list of projects, and if only one exists that one will be used. If multiple projects exist, an error will be thrown.

``service_name`` (optional)
:    The name of the Kafka service in the used project. If not specified, *upcheck* will search for Kafka services in that project, and if only one service is found, that one will be used. If multiple Kafka services exist, an error will be thrown.

#### Example configs

##### Using username and password to authencicate

{{ inline_file_as_codeblock('examples/kafka_target_aiven.yaml', format="yaml") }}

##### Using an authentication token to authencicate

{{ inline_file_as_codeblock('examples/kafka_target_aiven_token.yaml', format="yaml") }}

### target: postgres

Writes check results to a table in a Postgres database.

Currently, it's not possible to specify the table name to write to, it's hardcoded as 'check_results'. To create that table, please run the ``schema.sql`` from: https://gitlab.com/makkus/upcheck/-/blob/develop/db/schema.sql

#### Configuration

``type`` (required value: ``psotgres``)
:    The target type.

``username`` (required)
:    The username to authenticate against the Postgres database.

``password`` (required)
:    The password to authenticate against the Postgres database.

``dbname`` (required)
:    The databsae name.

``host`` (optional, defaults to ``localhost``)
:    The host that runs the Postgres database service.

``port`` (optional, defaults to ``5432``
:    The port the Postgres database service listens on.

``sslmode`` (optional)
:    The ssl mode to use.

``sslrootcert`` (optional)
:    The path to a ssl root certificate, used to verify the server certificate.

#### Example configs

##### Postgres target using username/password auth, verifying server cert

{{ inline_file_as_codeblock('examples/postgres_target.yaml', format="yaml") }}

### target: postgres-aiven

A convenience wrapper target, in case you are using [aiven](https://aiven.io) to run your Postgres database service. It removes most of the configuration options, and figures most configuration values (certs, etc.) out by itself, using the Aiven REST API.

Use like:

```console
> upcheck check --target /home/markus/postgres_target_aiven.yaml https://frkl.io
```

#### Configuration

``type``: (required value: ``postgres-aiven``)
:    The target type.

``dbname`` (required)
:    The database name.

``password`` (required)
:    An authentication token for the Aiven API, or the account password if using ``email`` (below).

``email`` (optional)
:    If a value for the ``email`` is specified, *upcheck* assumes username/password authentication instead of the token-based one.

``project_name`` (optional)
:    The project name. If not specified, *upcheck* checks the list of projects, and if only one exists that one will be used. If multiple projects exist, an error will be thrown.

``service_name`` (optional)
:    The name of the Postgres service in the used project. If not specified, *upcheck* will search for Postgres services in that project, and if only one service is found, that one will be used. If multiple Postgres services exist, an error will be thrown.


#### Example configs

##### Using username and password to authencicate

{{ inline_file_as_codeblock('examples/postgres_target_aiven.yaml', format="yaml") }}

##### Using an authentication token to authencicate

{{ inline_file_as_codeblock('examples/postgres_target_aiven_token.yaml', format="yaml") }}
