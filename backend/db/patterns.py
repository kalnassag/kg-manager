"""Pattern management for visual query builder."""
from typing import Dict, List, Optional
from datetime import datetime
from .connection import get_connection
import json
import logging

logger = logging.getLogger(__name__)

class PatternManager:
    """Manages saved query patterns."""

    def __init__(self):
        self.conn = get_connection()
        self._ensure_pattern_nodes()

    def _ensure_pattern_nodes(self):
        """Ensure SavedPattern nodes exist in database."""
        query = """
        MERGE (root:PatternRoot {id: 'root'})
        RETURN root
        """
        try:
            self.conn.execute_query(query)
            logger.info("Pattern storage initialized")
        except Exception as e:
            logger.error(f"Failed to initialize pattern storage: {e}")

    def save_pattern(self, pattern_data: Dict) -> Dict:
        """
        Save a query pattern.

        Args:
            pattern_data: {
                'name': str,
                'description': str,
                'pattern_json': dict,  # Visual pattern definition
                'cypher_query': str,   # Generated Cypher
                'created_by': str (optional)
            }

        Returns:
            Saved pattern with ID
        """
        pattern_id = f"pattern_{datetime.now().timestamp()}"

        query = """
        CREATE (p:SavedPattern {
            id: $id,
            name: $name,
            description: $description,
            pattern_json: $pattern_json,
            cypher_query: $cypher_query,
            created_by: $created_by,
            created_at: datetime(),
            updated_at: datetime()
        })
        RETURN p
        """

        try:
            result = self.conn.execute_query(query, {
                'id': pattern_id,
                'name': pattern_data.get('name', 'Untitled Pattern'),
                'description': pattern_data.get('description', ''),
                'pattern_json': json.dumps(pattern_data.get('pattern_json', {})),
                'cypher_query': pattern_data.get('cypher_query', ''),
                'created_by': pattern_data.get('created_by', 'anonymous')
            })

            if result:
                saved_pattern = dict(result[0]['p'])
                # Parse JSON string back to dict
                saved_pattern['pattern_json'] = json.loads(saved_pattern['pattern_json'])
                logger.info(f"Saved pattern: {pattern_id}")
                return saved_pattern

            raise Exception("Failed to save pattern")

        except Exception as e:
            logger.error(f"Error saving pattern: {e}")
            raise

    def get_pattern(self, pattern_id: str) -> Optional[Dict]:
        """Get a single pattern by ID."""
        query = """
        MATCH (p:SavedPattern {id: $id})
        RETURN p
        """

        try:
            result = self.conn.execute_query(query, {'id': pattern_id})
            if result:
                pattern = dict(result[0]['p'])
                pattern['pattern_json'] = json.loads(pattern['pattern_json'])
                return pattern
            return None
        except Exception as e:
            logger.error(f"Error retrieving pattern: {e}")
            return None

    def list_patterns(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List all saved patterns."""
        query = """
        MATCH (p:SavedPattern)
        RETURN p
        ORDER BY p.created_at DESC
        SKIP $offset
        LIMIT $limit
        """

        try:
            results = self.conn.execute_query(query, {
                'offset': offset,
                'limit': limit
            })

            patterns = []
            for record in results:
                pattern = dict(record['p'])
                pattern['pattern_json'] = json.loads(pattern['pattern_json'])
                patterns.append(pattern)

            return patterns
        except Exception as e:
            logger.error(f"Error listing patterns: {e}")
            return []

    def update_pattern(self, pattern_id: str, updates: Dict) -> Optional[Dict]:
        """Update a pattern."""
        # Build SET clause dynamically
        set_clauses = []
        params = {'id': pattern_id}

        allowed_fields = ['name', 'description', 'pattern_json', 'cypher_query']
        for field in allowed_fields:
            if field in updates:
                set_clauses.append(f"p.{field} = ${field}")
                value = updates[field]
                if field == 'pattern_json':
                    value = json.dumps(value)
                params[field] = value

        if not set_clauses:
            return self.get_pattern(pattern_id)

        set_clauses.append("p.updated_at = datetime()")

        query = f"""
        MATCH (p:SavedPattern {{id: $id}})
        SET {', '.join(set_clauses)}
        RETURN p
        """

        try:
            result = self.conn.execute_query(query, params)
            if result:
                pattern = dict(result[0]['p'])
                pattern['pattern_json'] = json.loads(pattern['pattern_json'])
                logger.info(f"Updated pattern: {pattern_id}")
                return pattern
            return None
        except Exception as e:
            logger.error(f"Error updating pattern: {e}")
            return None

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern."""
        query = """
        MATCH (p:SavedPattern {id: $id})
        DELETE p
        """

        try:
            self.conn.execute_write(query, {'id': pattern_id})
            logger.info(f"Deleted pattern: {pattern_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting pattern: {e}")
            return False

    def search_patterns(self, search_term: str) -> List[Dict]:
        """Search patterns by name or description."""
        query = """
        MATCH (p:SavedPattern)
        WHERE toLower(p.name) CONTAINS toLower($term)
           OR toLower(p.description) CONTAINS toLower($term)
        RETURN p
        ORDER BY p.created_at DESC
        LIMIT 50
        """

        try:
            results = self.conn.execute_query(query, {'term': search_term})
            patterns = []
            for record in results:
                pattern = dict(record['p'])
                pattern['pattern_json'] = json.loads(pattern['pattern_json'])
                patterns.append(pattern)
            return patterns
        except Exception as e:
            logger.error(f"Error searching patterns: {e}")
            return []

# Global pattern manager instance
_pattern_manager: Optional[PatternManager] = None

def get_pattern_manager() -> PatternManager:
    """Get the global pattern manager instance."""
    global _pattern_manager
    if _pattern_manager is None:
        _pattern_manager = PatternManager()
    return _pattern_manager
