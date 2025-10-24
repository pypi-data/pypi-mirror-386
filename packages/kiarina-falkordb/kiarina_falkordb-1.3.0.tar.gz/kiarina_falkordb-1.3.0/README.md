[![license](https://img.shields.io/github/license/kiarina/falkordb-py.svg)](https://github.com/kiarina/falkordb-py)
[![Release](https://img.shields.io/github/release/kiarina/falkordb-py.svg)](https://github.com/kiarina/falkordb-py/releases/latest)
[![PyPI version](https://badge.fury.io/py/kiarina-falkordb.svg)](https://badge.fury.io/py/kiarina-falkordb)

# kiarina-falkordb

> **ℹ️ This is a fork of [falkordb-py](https://github.com/FalkorDB/falkordb-py) with additional fixes.**
>
> **Original work by the [FalkorDB team](https://github.com/FalkorDB/falkordb-py).**
>
> This fork includes bug fixes and improvements that are pending upstream merge.

[![Try Free](https://img.shields.io/badge/Try%20Free-FalkorDB%20Cloud-FF8101?labelColor=FDE900&style=for-the-badge&link=https://app.falkordb.cloud)](https://app.falkordb.cloud)

FalkorDB Python client

see [docs](http://falkordb-py.readthedocs.io/)

## Installation
```sh
pip install kiarina-falkordb
```

## Differences from upstream

- ✅ **redis-py 7.0.0 support** - Compatible with redis-py >= 7.0.0
- ✅ **Python 3.9+ required** - Dropped Python 3.8 support for redis-py 7.x compatibility
- ✅ Fixed async `from_url()` to correctly use host/port from URL
- ✅ All original functionality preserved
- 🔄 Actively maintained with upstream compatibility

## Usage

### Run FalkorDB instance
Docker:
```sh
docker run --rm -p 6379:6379 falkordb/falkordb
```
Or use [FalkorDB Cloud](https://app.falkordb.cloud)

### Synchronous Example

```python
from falkordb import FalkorDB

# Connect to FalkorDB
db = FalkorDB(host='localhost', port=6379)

# Select the social graph
g = db.select_graph('social')

# Create 100 nodes and return a handful
nodes = g.query('UNWIND range(0, 100) AS i CREATE (n {v:1}) RETURN n LIMIT 10').result_set
for n in nodes:
    print(n)

# Read-only query the graph for the first 10 nodes
nodes = g.ro_query('MATCH (n) RETURN n LIMIT 10').result_set

# Copy the Graph
copy_graph = g.copy('social_copy')

# Delete the Graph
g.delete()
```

### Asynchronous Example

```python
import asyncio
from falkordb.asyncio import FalkorDB
from redis.asyncio import BlockingConnectionPool

async def main():

    # Connect to FalkorDB
    pool = BlockingConnectionPool(max_connections=16, timeout=None, decode_responses=True)
    db = FalkorDB(connection_pool=pool)

    # Select the social graph
    g = db.select_graph('social')

    # Execute query asynchronously
    result = await g.query('UNWIND range(0, 100) AS i CREATE (n {v:1}) RETURN n LIMIT 10')

    # Process results
    for n in result.result_set:
        print(n)

    # Run multiple queries concurrently
    tasks = [
        g.query('MATCH (n) WHERE n.v = 1 RETURN count(n) AS count'),
        g.query('CREATE (p:Person {name: "Alice"}) RETURN p'),
        g.query('CREATE (p:Person {name: "Bob"}) RETURN p')
    ]

    results = await asyncio.gather(*tasks)

    # Process concurrent results
    print(f"Node count: {results[0].result_set[0][0]}")
    print(f"Created Alice: {results[1].result_set[0][0]}")
    print(f"Created Bob: {results[2].result_set[0][0]}")

    # Close the connection when done
    await pool.aclose()

# Run the async example
if __name__ == "__main__":
    asyncio.run(main())
```

## Development

### Running Tests

Start a FalkorDB instance:
```sh
docker run -d --rm --name falkordb-test -p 6379:6379 falkordb/falkordb:latest
```

Install dependencies and run tests:
```sh
poetry install
poetry run pytest -v
```

Stop the test instance:
```sh
docker stop falkordb-test
```

### Release

Build and publish to PyPI:
```sh
poetry build
poetry publish
```
