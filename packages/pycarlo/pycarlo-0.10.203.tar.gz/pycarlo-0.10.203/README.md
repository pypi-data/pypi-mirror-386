# Pycarlo

Monte Carlo's Alpha Python SDK!

## Installation

Requires Python 3.9 or greater. Normally you can install and update using pip. For instance:

```shell
virtualenv venv
. venv/bin/activate

pip install -U pycarlo
```

Developers of the SDK can use:

```shell
make install-with-tests
. venv/bin/activate
pre-commit install
```

## Overview

Pycarlo comprises two components: `core` and `features`.

All Monte Carlo API queries and mutations that you could execute via the API are supported via the `core` library. Operations can be executed as first class objects, using [sgqlc](https://github.com/profusion/sgqlc), or as raw GQL with variables. In both cases, a consistent object where fields can be referenced by dot notation and the more pythonic snake_case is returned for ease of use.

The `features` library provides additional convenience for performing common operations like with dbt, circuit breaking, and pii filtering.

Note that an API Key is required to use the SDK. See [here](https://docs.getmontecarlo.com/docs/developer-resources#creating-an-api-key) for details on how to generate one.

## Basic usage

### Core

```python
from pycarlo.core import Client, Query, Mutation

# First create a client. This creates a session using the 'default' profile from
# '~/.mcd/profiles.ini'. This profile is created automatically via
# `montecarlo configure` on the CLI. See the session subsection for
# customizations, options and alternatives (e.g. using the environment, params,
# named profiles, etc.)
client = Client()

# Now you can can execute a query. For instance, getUser (selecting the email field).
# This would be like executing -
#     curl --location --request POST 'https://api.getmontecarlo.com/graphql' \
#     --header 'x-mcd-id: <ID>' \
#     --header 'x-mcd-token: <TOKEN>' \
#     --header 'Content-Type: application/json' \
#     --data-raw '{"query": "query {getUser {email}}"}'
# Notice how the CamelCase from the Graphql query is converted to snake_case in
# both the request and response.
query = Query()
query.get_user.__fields__('email')
print(client(query).get_user.email)

# You can also execute a query that requires variables. For instance,
# testTelnetConnection (selecting all fields).
query = Query()
query.test_telnet_connection(host='montecarlodata.com', port=443)
print(client(query))

# If necessary, you can always generate (e.g. print) the raw query that would be executed.
print(query)
# query {
#   testTelnetConnection(host: "montecarlodata.com", port: 443) {
#     success
#     validations {
#       type
#       message
#     }
#     warnings {
#       type
#       message
#     }
#   }
# }

# If you are not a fan of sgqlc operations (Query and Mutation) you can also execute any
# raw query using the client. For instance, if we want the first 10 tables from getTables.
get_table_query = """
query getTables{
  getTables(first: 10) {
    edges {
      node {
        fullTableId
      }
    }
  }
}
"""
response = client(get_table_query)
# This returns a Box object where fields can be accessed using dot notation.
# Notice how unlike with the API the response uses the more Pythonic snake_case.
for edge in response.get_tables.edges:
    print(edge.node.full_table_id)
# The response can still be processed as a standard dictionary.
print(response['get_tables']['edges'][0]['node']['full_table_id'])

# You can also execute any mutations too. For instance, generateCollectorTemplate
# (selecting the templateLaunchUrl).
mutation = Mutation()
mutation.generate_collector_template().dc.template_launch_url()
print(client(mutation))

# Any errors will raise a GqlError with details. For instance, executing above with an
# invalid region.
mutation = Mutation()
mutation.generate_collector_template(region='artemis')
print(client(mutation))
# pycarlo.common.errors.GqlError: [
#   {'message': 'Region "\'artemis\'" not currently active.'...
# ]
```

Note that you can find Monte Carlo's API reference [here](https://apidocs.getmontecarlo.com/).

For details and additional examples on how to map (convert) GraphQL queries to `sgqlc` operations please refer to the docs [here](https://sgqlc.readthedocs.io/en/latest/sgqlc.operation.html).

### Features

You can use [pydoc](https://docs.python.org/3.8/library/pydoc.html) to retrieve documentation on any feature packages (`pydoc pycarlo.features`).

For instance for [circuit breakers](https://docs.getmontecarlo.com/docs/circuit-breakers):

```shell
pydoc pycarlo.features.circuit_breakers.service
```

## Session configuration

By default, when creating a client the `default` profile from `~/.mcd/profiles.ini` is used. This file created via [montecarlo configure](https://docs.getmontecarlo.com/docs/using-the-cli#setting-up-the-cli) on the CLI. Note that you can find Monte Carlo's CLI reference [here](https://clidocs.getmontecarlo.com/).

You can override this usage by creating a custom `Session`. For instance, if you want to pass the ID and Token:

```python
from pycarlo.core import Client, Session

client = Client(session=Session(mcd_id='foo', mcd_token='bar'))
```

Sessions support the following params:

- `mcd_id`: API Key ID.
- `mcd_token`: API secret.
- `mcd_profile`: Named profile containing credentials. This is created via the CLI (e.g. `montecarlo configure --profile-name zeus`).
- `mcd_config_path`: Path to file containing credentials. Defaults to `~/.mcd/`.

You can also specify the API Key, secret or profile name using the following environment variables:

- `MCD_DEFAULT_API_ID`
- `MCD_DEFAULT_API_TOKEN`
- `MCD_DEFAULT_PROFILE`

When creating a session any explicitly passed `mcd_id` and `mcd_token` params take precedence, followed by environmental variables and then any config-file options.

Environment variables can be mixed with passed credentials, but not the config-file profile.

**We do not recommend passing `mcd_token` as it is a secret and can be accidentally committed.**

## Integration Gateway API

There are features that require the Integration Gateway API instead of the regular GraphQL Application API, for example Airflow Callbacks invoked by the `airflow-mcd` library.

To use the Gateway you need to initialize the `Session` object passing a `scope` parameter and then use `make_request` to invoke Gateway endpoints:

```python
from pycarlo.core import Client, Session

client = Client(session=Session(mcd_id='foo', mcd_token='bar', scope='AirflowCallbacks'))
response = client.make_request(
  path='/airflow/callbacks', method='POST', body={}, timeout_in_seconds=20
)
```

## Advanced configuration

The following values also be set by the environment:

- `MCD_VERBOSE_ERRORS`: Enable logging. This includes a trace ID for each session and request.
- `MCD_API_ENDPOINT`: Customize the endpoint where queries and mutations are executed.

## Tests and releases

To update queries and mutations via introspection, use `make generate`.

`make test` can be used to run all tests locally. CircleCI manages all testing for deployment. When ready for a review, create a PR against `main`.

When ready to release, create a new [Github release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) with a tag using semantic versioning (e.g. `v0.42.0`) and CircleCI will test and publish to PyPI. Note that an existing version will not be deployed.

## References

- Dashboard: <https://getmontecarlo.com>
- Product docs: <https://docs.getmontecarlo.com>
- Status page: <https://status.getmontecarlo.com>
- API (and SDK): <https://apidocs.getmontecarlo.com>
- CLI: <https://clidocs.getmontecarlo.com>

## License

Apache 2.0 - See the [LICENSE](http://www.apache.org/licenses/LICENSE-2.0) for more information.
