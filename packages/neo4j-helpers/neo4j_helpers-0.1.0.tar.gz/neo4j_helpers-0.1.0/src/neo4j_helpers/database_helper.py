from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from neo4j import GraphDatabase


def _escape_identifier(identifier: str) -> str:
    return identifier.replace("`", "``")


NEO4J_USERNAME = "neo4j"
LOCALHOST_DOMAIN = "bolt://localhost"
LOCALHOST_PORT = 7687
LOCALHOST_URI = f"{LOCALHOST_DOMAIN}:{LOCALHOST_PORT}"
INITIAL_PASSWORD = "neo4j"
DEFAULT_PASSWORD = "password"
DEFAULT_AUTH = (NEO4J_USERNAME, DEFAULT_PASSWORD)
DEFAULT_DATABASE = "neo4j"


@dataclass
class Neo4jInfo:
    """Connection information for a Neo4j instance."""

    uri: str
    auth: tuple[str, str]
    database: str
    version: int | None = None

    @staticmethod
    def GetDefaultLocalHost(db_name: str = DEFAULT_DATABASE, port = LOCALHOST_PORT) -> "Neo4jInfo":
        return Neo4jInfo(f"{LOCALHOST_DOMAIN}:{port}", DEFAULT_AUTH, db_name)


class Neo4jDatabaseHelper:
    """Thin convenience wrapper around the official Neo4j Python driver."""

    def __init__(self, neo4j_info: Neo4jInfo):
        self.neo4j_info = neo4j_info

    def can_connect(self) -> bool:
        with GraphDatabase.driver(self.neo4j_info.uri, auth=self.neo4j_info.auth) as driver:
            try:
                driver.verify_connectivity()
                return True
            except Exception:
                return False

    def is_db_exists(self, database_name: str | None = None) -> bool:
        target_db = database_name or self.neo4j_info.database
        with GraphDatabase.driver(self.neo4j_info.uri, auth=self.neo4j_info.auth) as driver:
            with driver.session(database="system") as session:
                return self.is_db_exists_inner(target_db, session)

    def is_db_exists_inner(self, target_db: str, session) -> bool:
        record = session.run(
            "SHOW DATABASES YIELD name WHERE name = $db RETURN count(name) AS count",
            db=target_db,
        ).single()
        return bool(record and record["count"])

    def create_db(self, database_name: str | None = None, *, if_not_exists: bool = True) -> None:
        target_db = database_name or self.neo4j_info.database
        escaped_name = _escape_identifier(target_db)
        clause = " IF NOT EXISTS" if if_not_exists else ""
        cypher = f"CREATE DATABASE `{escaped_name}`{clause} WAIT"

        with GraphDatabase.driver(self.neo4j_info.uri, auth=self.neo4j_info.auth) as driver:
            with driver.session(database="system") as session:
                session.run(cypher)

    def run_cypher(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        *,
        database_name: str | None = None,
    ) -> list[dict[str, Any]]:
        target_db = database_name or self.neo4j_info.database
        with GraphDatabase.driver(self.neo4j_info.uri, auth=self.neo4j_info.auth) as driver:
            with driver.session(database=target_db) as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]

    def count_nodes(self, *, database_name: str | None = None) -> int:
        query = "MATCH (n) RETURN count(n) AS total"
        records = self.run_cypher(query, database_name=database_name)
        return records[0]["total"] if records else 0

    def count_rels(self, *, database_name: str | None = None) -> int:
        query = "MATCH ()-[r]->() RETURN count(r) AS total"
        records = self.run_cypher(query, database_name=database_name)
        return records[0]["total"] if records else 0

    @contextmanager
    def open_connection(self, *, database_name: str | None = None):
        """Opens a scoped Neo4j session and ensures cleanup."""
        target_db = database_name or self.neo4j_info.database
        driver = GraphDatabase.driver(self.neo4j_info.uri, auth=self.neo4j_info.auth)
        try:
            with driver.session(database=target_db) as session:
                yield session
        finally:
            driver.close()

    def delete_db(
        self,
        database_name: str | None = None,
        *,
        if_exists: bool = True,
        if_destroy_data: bool = True,
    ) -> None:
        target_db = database_name or self.neo4j_info.database
        escaped_name = _escape_identifier(target_db)
        clause = " IF EXISTS" if if_exists else ""
        destroy_clause = " DESTROY DATA" if if_destroy_data else ""
        cypher = f"DROP DATABASE `{escaped_name}`{clause}{destroy_clause} WAIT"

        with GraphDatabase.driver(self.neo4j_info.uri, auth=self.neo4j_info.auth) as driver:
            with driver.session(database="system") as session:
                session.run(cypher)


__all__ = [
    "Neo4jDatabaseHelper",
    "Neo4jInfo",
    "DEFAULT_AUTH",
    "DEFAULT_DATABASE",
    "DEFAULT_PASSWORD",
    "INITIAL_PASSWORD",
    "LOCALHOST_URI",
    "NEO4J_USERNAME",
]
