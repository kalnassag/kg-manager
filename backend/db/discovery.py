"""Discovery system for Neo4j graph schema."""
from typing import Dict, List, Set, Tuple
from .connection import get_connection
import logging

logger = logging.getLogger(__name__)

class SchemaDiscovery:
    """Discovers and analyzes Neo4j graph schema."""

    def __init__(self):
        self.conn = get_connection()
        self._cache = {}

    def discover_node_labels(self) -> List[str]:
        """Discover all node labels in the database."""
        query = "CALL db.labels()"
        results = self.conn.execute_query(query)
        labels = [r['label'] for r in results]
        logger.info(f"Discovered {len(labels)} node labels: {labels}")
        return sorted(labels)

    def get_node_properties(self, label: str) -> Dict[str, Set[type]]:
        """Get all properties for a given node label with their types."""
        query = f"""
        MATCH (n:{label})
        UNWIND keys(n) AS key
        RETURN DISTINCT key,
               collect(DISTINCT type(n[key])) AS types
        ORDER BY key
        """
        results = self.conn.execute_query(query)

        properties = {}
        for record in results:
            prop_name = record['key']
            types = record['types']
            properties[prop_name] = set(types)

        logger.info(f"Found {len(properties)} properties for {label}")
        return properties

    def get_sample_node(self, label: str) -> dict:
        """Get a sample node for a given label."""
        query = f"MATCH (n:{label}) RETURN n LIMIT 1"
        results = self.conn.execute_query(query)
        if results:
            return dict(results[0]['n'])
        return {}

    def get_node_count(self, label: str) -> int:
        """Get count of nodes with given label."""
        query = f"MATCH (n:{label}) RETURN count(n) as count"
        results = self.conn.execute_query(query)
        return results[0]['count'] if results else 0

    def categorize_labels(self, labels: List[str]) -> Tuple[List[str], List[str]]:
        """
        Categorize labels into product types and supporting entities.

        Heuristic: Labels with many properties (>10 avg) are likely products,
        others are supporting entities.
        """
        products = []
        supporting = []

        for label in labels:
            props = self.get_node_properties(label)
            avg_props = len(props)

            # Additional heuristic: check if it has product-like properties
            has_product_props = any(
                key.startswith(('product_', 'design_', 'inside_', 'display_'))
                for key in props.keys()
            )

            if avg_props > 10 or has_product_props:
                products.append(label)
            else:
                supporting.append(label)

        logger.info(f"Categorized: {len(products)} products, {len(supporting)} supporting entities")
        return sorted(products), sorted(supporting)

    def discover_relationships(self) -> List[Dict]:
        """Discover all relationship types in the database."""
        query = """
        CALL db.relationshipTypes() YIELD relationshipType
        RETURN relationshipType
        """
        results = self.conn.execute_query(query)
        rel_types = [r['relationshipType'] for r in results]

        # Get more details about each relationship
        relationships = []
        for rel_type in rel_types:
            # Get sample source and target labels
            query = f"""
            MATCH (a)-[r:{rel_type}]->(b)
            RETURN DISTINCT labels(a) as source_labels,
                   labels(b) as target_labels,
                   count(*) as count
            LIMIT 5
            """
            details = self.conn.execute_query(query)
            for detail in details:
                relationships.append({
                    'type': rel_type,
                    'source_labels': detail['source_labels'],
                    'target_labels': detail['target_labels'],
                    'count': detail['count']
                })

        logger.info(f"Discovered {len(rel_types)} relationship types")
        return relationships

    def get_entity_relationships(self, label: str, node_id: str) -> List[Dict]:
        """Get all relationships for a specific node."""
        # First, get the node
        query = f"""
        MATCH (n:{label} {{_id: $node_id}})
        RETURN n
        """
        node_results = self.conn.execute_query(query, {'node_id': node_id})
        if not node_results:
            return []

        # Get outgoing relationships
        query = f"""
        MATCH (n:{label} {{_id: $node_id}})-[r]->(m)
        RETURN type(r) as rel_type,
               labels(m) as target_labels,
               m as target_node,
               'outgoing' as direction
        """
        outgoing = self.conn.execute_query(query, {'node_id': node_id})

        # Get incoming relationships
        query = f"""
        MATCH (n:{label} {{_id: $node_id}})<-[r]-(m)
        RETURN type(r) as rel_type,
               labels(m) as source_labels,
               m as source_node,
               'incoming' as direction
        """
        incoming = self.conn.execute_query(query, {'node_id': node_id})

        relationships = []

        for rel in outgoing:
            relationships.append({
                'type': rel['rel_type'],
                'direction': 'outgoing',
                'node': dict(rel['target_node']),
                'labels': rel['target_labels']
            })

        for rel in incoming:
            relationships.append({
                'type': rel['rel_type'],
                'direction': 'incoming',
                'node': dict(rel['source_node']),
                'labels': rel['source_labels']
            })

        return relationships

    def get_all_schema_info(self) -> Dict:
        """Get comprehensive schema information."""
        labels = self.discover_node_labels()
        products, supporting = self.categorize_labels(labels)
        relationships = self.discover_relationships()

        schema = {
            'labels': labels,
            'product_types': products,
            'supporting_entities': supporting,
            'relationships': relationships,
            'counts': {label: self.get_node_count(label) for label in labels}
        }

        return schema

# Global discovery instance
_discovery: SchemaDiscovery = None

def get_discovery() -> SchemaDiscovery:
    """Get the global discovery instance."""
    global _discovery
    if _discovery is None:
        _discovery = SchemaDiscovery()
    return _discovery
