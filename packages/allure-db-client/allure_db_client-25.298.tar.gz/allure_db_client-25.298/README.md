# allure-db-client

A tiny helper around psycopg for running PostgreSQL queries in tests and utilities, with optional Allure reporting of executed SQL and results.

The package exposes two clients:
- DBClient — sync client (psycopg Connection)
- AsyncDBClient — async client (psycopg AsyncConnection)

Both clients support a small, convenient API for common cases and can be used as context managers to automatically open/close connections.

## Requirements
- Python 3.11
- PostgreSQL accessible via a connection string

## Installation
Install from PyPI:

```bash
pip install allure-db-client
```

Or with Poetry:

```bash
poetry add allure-db-client
```

## Connection string
Use a standard psycopg connection URI, for example:

```
postgresql://USER:PASSWORD@HOST:PORT/DBNAME
```

Example for local Dockerized Postgres:
```
postgresql://postgres:postgres@localhost:5432/postgres
```

## Quick start (sync)
```python
from allure_db_client import DBClient

conn_str = "postgresql://postgres:postgres@localhost:5432/postgres"

# with_allure=True will attach query and result to Allure report (if Allure is used in your tests)
with DBClient(connection_string=conn_str, with_allure=True) as db:
    # read examples
    rows = db.select_all("SELECT 1 AS one, 2 AS two")
    first_row = db.get_first_row("SELECT 42")         # -> (42,)
    first_value = db.get_first_value("SELECT 'hi'")   # -> 'hi'
    ids = db.get_list("SELECT generate_series(1, 3)") # -> [1, 2, 3]

    # get_dict expects first two columns to be key/value
    pairs = db.get_dict("SELECT 1, 'a' UNION ALL SELECT 2, 'b'") # -> {1: 'a', 2: 'b'}

    # write example
    db.execute("CREATE TEMP TABLE t(id int)")
    db.execute("INSERT INTO t(id) VALUES (%(id)s)", params={"id": 7})
```

## Quick start (async)
```python
import asyncio
from allure_db_client import AsyncDBClient

conn_str = "postgresql://postgres:postgres@localhost:5432/postgres"

async def main():
    async with AsyncDBClient(connection_string=conn_str, with_allure=True) as db:
        rows = await db.select_all("SELECT 1")
        value = await db.get_first_value("SELECT 'ok'")
        await db.execute("CREATE TEMP TABLE t(id int)")

asyncio.run(main())
```

## API overview
- select_all(query, params=None) -> list[tuple]
- get_first_row(query, params=None) -> tuple | None
- get_first_value(query, params=None) -> Any | None
- get_list(query, params=None) -> list[Any]
- get_dict(query, params=None) -> dict[Any, Any] | None
- execute(query, params=None) -> None

Notes:
- params is a dict passed to psycopg; use named placeholders like %(name)s in SQL.
- If with_allure=True, each call attaches the SQL and (for read queries) the result to the Allure report.

## Using with Allure
The clients can attach SQL and results to Allure steps when with_allure=True. Add allure-pytest to your test environment and run tests with Allure:

```bash
pip install allure-pytest
pytest --alluredir=./allure-results
```

Then open the report with your Allure CLI.

## Running tests locally
This repository includes a minimal test setup using Docker. It will start Postgres and run tests against it.

Prerequisites:
- Docker and docker-compose

Commands (from project root):

```bash
cd tests
docker compose up --build --abort-on-container-exit
```

The tests container will set PG_CONNECTION_STRING for the clients automatically, as defined in tests/docker-compose.yml.

## License
MIT — see LICENSE.
