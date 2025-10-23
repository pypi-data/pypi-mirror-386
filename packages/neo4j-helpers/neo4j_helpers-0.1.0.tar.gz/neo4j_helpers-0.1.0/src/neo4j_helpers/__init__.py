"""Convenience helpers for scripting Neo4j workloads and local deployments."""

from __future__ import annotations

from importlib import metadata

from .cypher_dispatcher import CypherDispatcher
from .database_helper import (
    DEFAULT_AUTH,
    DEFAULT_DATABASE,
    DEFAULT_PASSWORD,
    INITIAL_PASSWORD,
    LOCALHOST_URI,
    NEO4J_USERNAME,
    Neo4jDatabaseHelper,
    Neo4jInfo,
)
from .local_tools import Neo4jLocalTools
from .vector_tools import BvecReader, IvecReader

try:
    __version__ = metadata.version("neo4j-helpers")
except metadata.PackageNotFoundError:  # pragma: no cover - only in editable installs/tests
    __version__ = "0.1.0"

__all__ = [
    "BvecReader",
    "CypherDispatcher",
    "DEFAULT_AUTH",
    "DEFAULT_DATABASE",
    "DEFAULT_PASSWORD",
    "INITIAL_PASSWORD",
    "IvecReader",
    "LOCALHOST_URI",
    "NEO4J_USERNAME",
    "Neo4jDatabaseHelper",
    "Neo4jInfo",
    "Neo4jLocalTools",
    "__version__",
]
