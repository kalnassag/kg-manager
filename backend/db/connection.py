"""Neo4j database connection management."""
from neo4j import GraphDatabase
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Neo4jConnection:
    """Manages Neo4j database connections."""

    def __init__(self, uri: str, user: str, password: str):
        self._uri = uri
        self._user = user
        self._password = password
        self._driver: Optional[GraphDatabase.driver] = None

    def connect(self):
        """Establish connection to Neo4j."""
        try:
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password)
            )
            # Test connection
            self._driver.verify_connectivity()
            logger.info(f"Successfully connected to Neo4j at {self._uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close the Neo4j connection."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")

    def execute_query(self, query: str, parameters: dict = None):
        """Execute a Cypher query and return results."""
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")

        with self._driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(self, query: str, parameters: dict = None):
        """Execute a write query."""
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")

        with self._driver.session() as session:
            result = session.run(query, parameters or {})
            return result.consume()

# Global connection instance
_connection: Optional[Neo4jConnection] = None

def get_connection() -> Neo4jConnection:
    """Get the global Neo4j connection instance."""
    if _connection is None:
        raise RuntimeError("Neo4j connection not initialized")
    return _connection

def initialize_connection(uri: str, user: str, password: str):
    """Initialize the global Neo4j connection."""
    global _connection
    _connection = Neo4jConnection(uri, user, password)
    _connection.connect()

def close_connection():
    """Close the global Neo4j connection."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
