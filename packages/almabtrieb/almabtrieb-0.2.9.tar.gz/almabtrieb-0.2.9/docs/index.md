# almabtrieb

This is a client library for the [CattleDrive](https://helge.codeberg.page/cattle_grid/cattle_drive/) protocol as used by cattle_grid.

```mermaid
flowchart LR
    A@{ shape: processes, label: "Fediverse" }
    B@{ shape: lean-l, label: "cattle_grid" }

    A -->|ActivityPub| B
    B -->|CattleDrive| C(almabtrieb
powered
application)
```


This library enables one to create applications using cattle_grid as a middle ware to connect to the Fediverse. 
One can also use almabtrieb as a [cli tool](./cli.md) to inspect CattleDrive traffic.

## Sample Projects

- [cattle_grid_rss](https://codeberg.org/helge/cattle_grid_rss), see also the deployed version at [rss.bovine.social](https://rss.bovine.social).
- [roboherd](https://codeberg.org/bovine/roboherd)
- [cattle_grid](https://codeberg.org/bovine/cattle_grid/) in its feature tests

[comments](https://codeberg.org/bovine/comments/) directly subscribes to RabbitMQ,
but uses the CattleDrive protocol.

## Installation

For amqp, e.g. RabbitMQ

```bash
pip install almabtrieb[amqp]
```

For mqtt and mqtt over websockets

```bash
pip install almabtrieb[mqtt]   
```

## Usage

The following code example illustrates the usage of almabtrieb.

### Retrieving information about your account

```python
from almabtrieb import Almabtrieb

amqp_uri = "amqp://user:password@localhost:5672/"
connection = Almabtrieb.from_connection_string(amqp_uri)

async with connection:
    info = await connection.info()

    print("Your actors: ")
    for x in info.actors:
        print(f"{x.name}: {x.id}")
```

The response from info is of type [InformationResponse][almabtrieb.model.InformationResponse].
In the following, we will assume at least one actor exists, and we store
its id, i.e. the URI of the ActivityPub Actor object, in the `actor_id` variable.

```python
...
async with connection:
    ...
    actor_id = info.actors[0].id
```

### Fetching a remote oject

We can fetch a remote object with

```python
...
async with connection:
    ...

    result = await connection.fetch(actor_id, "http://remote.example/object/id")
    print(json.dumps(result.data["raw"], indent=2))
```

We note that data is of type [FetchResponse][almabtrieb.model.FetchResponse]

### Sending an activity

The following uses the default `send_message` method.

```python
...
async with connection:
    ...

    data = {
        "actor": actor_id,
        "message": {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Follow",
            "actor": actor_id,
            "object": "https://remote.actor/actor/id"
        }
    }
    await connection.trigger("send_message", data)
```

For information on the methods used see [Almabtrieb][almabtrieb.Almabtrieb].

### usage from command line

One can similarly use almabtrieb over the command line. First set the
`CONNECTION_STRING` environment varialbe to your connection, e.g.

```bash
export CONNECTION_STRING="amqp://user:password@localhost:5672/"
```

Then you can retrieve the information response via

```bash
python -malmabtrieb info

ACTORS:
from drive:                    http://abel/actor/-GiFasOk_NyC02ek0s9ayQ
```

Retrieving a remote object can then be done with

```bash
python -malmabtrieb fetch \
    http://abel/actor/-GiFasOk_NyC02ek0s9ayQ \
    http://remote.example/object/id
```

For more information on the command line tool, see [here](./cli.md)


## Developing

To start development clone the repository

```bash
git clone https://codeberg.org/bovine/almabtrieb.git
```

and install dependencies

```bash
uv sync --all-extras
```

By including the `--all-extras` flag one installs both the `amqp` and `mqtt`
dependencies mentioned in [installation](#installation).


### Running tests

Tests can be run with

```bash
uv run pytest
```

### Formatting and linting

One can check format and lint via

```bash
uv run ruff format
uv run ruff check
uv run pyright
```

### Running tests against cattle_grid

Create an account on cattle_grid with

```bash
python -mcattle_grid account new almabtrieb password --admin
```

Then with cattle grid running one can run

```bash
CONNECTION_STRING=mqtt://almabtrieb:password@localhost:11883 \
    uv run pytest almabtrieb/test_real.py
CONNECTION_STRING=ws://almabtrieb:password@localhost:15675/ws \
    uv run pytest almabtrieb/test_real.py
CONNECTION_STRING="amqp://almabtrieb:password@localhost:5672/" \
    uv run pytest almabtrieb/test_real.py
```

!!! todo
    One should also be able to support checking
    the secure variants `mqtts`, `amqps` and `wss`
    against the local `cattle_grid` instance. However, this
    requires appropriate certificate setups.
