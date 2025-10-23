"""Neo4j query functions for CRUD operations."""
from typing import Dict, List, Optional
from .connection import get_connection
import logging

logger = logging.getLogger(__name__)

class EntityQueries:
    """Handles all entity-related queries."""

    def __init__(self):
        self.conn = get_connection()

    def get_entities(self, label: str, page: int = 1, page_size: int = 100,
                     search: Optional[str] = None) -> Dict:
        """
        Get paginated list of entities for a given label.

        Returns: {
            'items': [...],
            'total': int,
            'page': int,
            'page_size': int,
            'total_pages': int
        }
        """
        # Count total
        count_query = f"MATCH (n:{label})"
        if search:
            count_query += " WHERE any(prop IN keys(n) WHERE toString(n[prop]) CONTAINS $search)"
        count_query += " RETURN count(n) as total"

        count_result = self.conn.execute_query(
            count_query,
            {'search': search} if search else {}
        )
        total = count_result[0]['total'] if count_result else 0

        # Get paginated results
        skip = (page - 1) * page_size
        query = f"MATCH (n:{label})"
        if search:
            query += " WHERE any(prop IN keys(n) WHERE toString(n[prop]) CONTAINS $search)"
        query += " RETURN n ORDER BY n._id SKIP $skip LIMIT $limit"

        results = self.conn.execute_query(
            query,
            {
                'skip': skip,
                'limit': page_size,
                'search': search
            } if search else {
                'skip': skip,
                'limit': page_size
            }
        )

        items = [dict(r['n']) for r in results]

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        }

    def get_entity_by_id(self, label: str, entity_id: str) -> Optional[Dict]:
        """Get a single entity by its ID."""
        query = f"MATCH (n:{label} {{_id: $id}}) RETURN n"
        results = self.conn.execute_query(query, {'id': entity_id})

        if results:
            return dict(results[0]['n'])
        return None

    def create_entity(self, label: str, properties: Dict) -> Dict:
        """Create a new entity."""
        # Build property string
        query = f"CREATE (n:{label} $props) RETURN n"

        result = self.conn.execute_query(query, {'props': properties})

        if result:
            logger.info(f"Created {label} entity with id: {properties.get('_id')}")
            return dict(result[0]['n'])

        raise Exception("Failed to create entity")

    def update_entity(self, label: str, entity_id: str, properties: Dict) -> Dict:
        """Update an existing entity."""
        # Remove _id from properties if present (can't change ID)
        props = {k: v for k, v in properties.items() if k != '_id'}

        query = f"""
        MATCH (n:{label} {{_id: $id}})
        SET n += $props
        RETURN n
        """

        result = self.conn.execute_query(
            query,
            {'id': entity_id, 'props': props}
        )

        if result:
            logger.info(f"Updated {label} entity: {entity_id}")
            return dict(result[0]['n'])

        raise Exception("Entity not found or update failed")

    def delete_entity(self, label: str, entity_id: str) -> bool:
        """Delete an entity (detach delete to remove relationships)."""
        query = f"MATCH (n:{label} {{_id: $id}}) DETACH DELETE n"

        self.conn.execute_write(query, {'id': entity_id})
        logger.info(f"Deleted {label} entity: {entity_id}")
        return True

    def create_relationship(self, source_label: str, source_id: str,
                          rel_type: str, target_label: str, target_id: str) -> bool:
        """Create a relationship between two entities."""
        query = f"""
        MATCH (a:{source_label} {{_id: $source_id}})
        MATCH (b:{target_label} {{_id: $target_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        RETURN r
        """

        result = self.conn.execute_query(
            query,
            {
                'source_id': source_id,
                'target_id': target_id
            }
        )

        if result:
            logger.info(f"Created relationship {source_label}({source_id})-[{rel_type}]->{target_label}({target_id})")
            return True

        return False

    def delete_relationship(self, source_label: str, source_id: str,
                          rel_type: str, target_label: str, target_id: str) -> bool:
        """Delete a specific relationship between two entities."""
        query = f"""
        MATCH (a:{source_label} {{_id: $source_id}})-[r:{rel_type}]->(b:{target_label} {{_id: $target_id}})
        DELETE r
        """

        self.conn.execute_write(
            query,
            {
                'source_id': source_id,
                'target_id': target_id
            }
        )

        logger.info(f"Deleted relationship {source_label}({source_id})-[{rel_type}]->{target_label}({target_id})")
        return True

    def search_entities(self, search_term: str, labels: Optional[List[str]] = None) -> List[Dict]:
        """
        Search across entities.

        If labels is None, search all labels.
        """
        if labels:
            label_filter = ':' + '|'.join(labels)
        else:
            label_filter = ''

        query = f"""
        MATCH (n{label_filter})
        WHERE any(prop IN keys(n) WHERE toString(n[prop]) CONTAINS $search)
        RETURN n, labels(n) as labels
        LIMIT 100
        """

        results = self.conn.execute_query(query, {'search': search_term})

        items = []
        for r in results:
            item = dict(r['n'])
            item['_labels'] = r['labels']
            items.append(item)

        return items

    def get_relationship_counts(self, label: str, entity_id: str) -> Dict[str, int]:
        """Get counts of related entities by relationship type."""
        query = f"""
        MATCH (n:{label} {{_id: $id}})
        OPTIONAL MATCH (n)-[r]->(m)
        WITH n, type(r) as rel_type, count(m) as outgoing_count
        OPTIONAL MATCH (n)<-[r2]-(m2)
        WITH n, rel_type, outgoing_count, type(r2) as incoming_rel_type, count(m2) as incoming_count
        RETURN rel_type, outgoing_count, incoming_rel_type, incoming_count
        """

        results = self.conn.execute_query(query, {'id': entity_id})

        counts = {}
        for r in results:
            if r['rel_type']:
                counts[f"{r['rel_type']}_out"] = r['outgoing_count']
            if r['incoming_rel_type']:
                counts[f"{r['incoming_rel_type']}_in"] = r['incoming_count']

        return counts

# Global queries instance
_queries: EntityQueries = None

def get_queries() -> EntityQueries:
    """Get the global queries instance."""
    global _queries
    if _queries is None:
        _queries = EntityQueries()
    return _queries
