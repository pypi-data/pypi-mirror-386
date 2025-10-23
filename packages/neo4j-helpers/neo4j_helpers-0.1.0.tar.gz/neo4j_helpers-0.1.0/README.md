# neo4j-helpers

Utilities for scripting Neo4j workflows from Python. The package bundles a
handful of small helpers you can mix and match:

- `Neo4jDatabaseHelper` – thin wrapper around the official driver for common admin tasks
- `CypherDispatcher` – thread-based worker pool for running a Cypher statement concurrently
- `Neo4jLocalTools` – utilities for working with a locally installed Neo4j distribution
- `BvecReader` / `IvecReader` – streaming readers for ANN vector datasets (Faiss `.bvecs/.ivecs`)

The project currently targets Python 3.10+ and the Neo4j Python driver >= 5.0.

## Installation

```bash
pip install neo4j-helpers
```

Or, for local development inside this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev]'
```

## Quickstart

```python
from neo4j_helpers import (
    CypherDispatcher,
    Neo4jDatabaseHelper,
    Neo4jInfo,
    Neo4jLocalTools,
)

neo_info = Neo4jInfo.GetDefaultLocalHost()
helper = Neo4jDatabaseHelper(neo_info)

if not helper.is_db_exists():
    helper.create_db()

with CypherDispatcher(neo_info, "CREATE (:Person {name: $name})") as dispatcher:
    for name in ["Ada", "Grace", "Linus"]:
        dispatcher.submit({"name": name})

local = Neo4jLocalTools("~/neo4j/instances/local")
local.start_server(wait=True)
# ...
local.stop_server(wait=True)
```

Vector dataset helpers stream binary records without loading entire files:

```python
from neo4j_helpers import BvecReader

reader = BvecReader("~/bigann/bigann_base.bvecs.gz")
for vector in reader.iter_vectors(limit=2):
    print(len(vector), vector[:8])
```

## Development Workflow

- Run the test suite with `python3 -m pytest`
- Linting relies on the standard library `venv` + `pip install -e '.[dev]'`
- Temporary environment variables used in examples:
  ```bash
  export VECTOR_FILTER_BVECS_PATH='~/bigann/bigann_base.bvecs.gz'
  export VECTOR_FILTER_IMPORT_DIR='~/neo4j/import/sample-dbs/vector-filter-v2'
  export NEO4J_HOME='~/neo4j/instances/local/'
  ```

## Releasing

1. Update `pyproject.toml` and `src/neo4j_helpers/__init__.py` with the next version.
2. Build the distribution artifacts:
   ```bash
   python -m build
   ```
3. Inspect the generated `dist/` archives (optional but recommended).
4. Upload to PyPI (or TestPyPI first):
   ```bash
   twine upload dist/*
   ```

If you are publishing to TestPyPI, pass `--repository testpypi` to `twine upload`.

## Internal Reference Notes

These notes remain from the original utilities project – feel free to move them
elsewhere if they no longer belong in the public README.

- Authenticate with Google Cloud:
  ```bash
  gcloud auth application-default login --no-launch-browser
  gcloud compute config-ssh
  ```
- JVM tuning for vector imports (requires a JDK providing incubator vectors):
  ```bash
  export JVM_OPTS="--add-modules jdk.incubator.vector"
  ```
- Sample inline Neo4j admin import command:
  ```bash
  /opt/neo4j/bin/neo4j-admin database import full \
      --schema=/mnt/neo4j-import/sample-dbs/vector-filter-v2/vector-filter-schema.cypher \
      --nodes=CHUNK=/mnt/neo4j-import/sample-dbs/vector-filter-v2/chunks.csv \
      --nodes=DOCUMENT=/mnt/neo4j-import/sample-dbs/vector-filter-v2/documents.csv \
      --nodes=PROJECT=/mnt/neo4j-import/sample-dbs/vector-filter-v2/projects.csv \
      --nodes=AUTHOR=/mnt/neo4j-import/sample-dbs/vector-filter-v2/authors.csv \
      --relationships=PART_OF=/mnt/neo4j-import/sample-dbs/vector-filter-v2/chunk-doc.csv \
      --relationships=WRITTEN_FOR=/mnt/neo4j-import/sample-dbs/vector-filter-v2/doc-proj.csv \
      --relationships=WRITTEN_BY=/mnt/neo4j-import/sample-dbs/vector-filter-v2/doc-author.csv \
      --overwrite-destination=true \
      --report-file=/mnt/neo4j-import/sample-dbs/vector-filter-v2/report.txt \
      --verbose \
      vector.filter.v2
  ```
