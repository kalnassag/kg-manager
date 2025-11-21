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
        RETURN DISTINCT key
        ORDER BY key
        """
        results = self.conn.execute_query(query)

        properties = {}
        for record in results:
            prop_name = record['key']
            # We use a placeholder set - actual type validation is done by naming convention
            properties[prop_name] = set()

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
        """Get all relationships for a specific node (tries multiple identifier properties)."""
        # Try to find the node with different ID properties
        id_properties = ['_id', 'id', 'name', 'model', 'code']
        node_found = False
        id_prop_used = '_id'

        for id_prop in id_properties:
            query = f"MATCH (n:{label} {{{id_prop}: $node_id}}) RETURN n"
            try:
                node_results = self.conn.execute_query(query, {'node_id': node_id})
                if node_results:
                    node_found = True
                    id_prop_used = id_prop
                    break
            except:
                continue

        if not node_found:
            # Try matching any property
            query = f"""
            MATCH (n:{label})
            WHERE any(prop IN keys(n) WHERE toString(n[prop]) = $node_id)
            RETURN n
            LIMIT 1
            """
            try:
                node_results = self.conn.execute_query(query, {'node_id': node_id})
                if node_results:
                    node_found = True
                    # For this case, we'll use a dynamic match in relationship queries
                    id_prop_used = None
            except:
                pass

        if not node_found:
            return []

        # Get outgoing relationships
        if id_prop_used:
            query = f"""
            MATCH (n:{label} {{{id_prop_used}: $node_id}})-[r]->(m)
            RETURN type(r) as rel_type,
                   labels(m) as target_labels,
                   m as target_node,
                   'outgoing' as direction
            """
        else:
            query = f"""
            MATCH (n:{label})-[r]->(m)
            WHERE any(prop IN keys(n) WHERE toString(n[prop]) = $node_id)
            RETURN type(r) as rel_type,
                   labels(m) as target_labels,
                   m as target_node,
                   'outgoing' as direction
            LIMIT 1000
            """
        outgoing = self.conn.execute_query(query, {'node_id': node_id})

        # Get incoming relationships
        if id_prop_used:
            query = f"""
            MATCH (n:{label} {{{id_prop_used}: $node_id}})<-[r]-(m)
            RETURN type(r) as rel_type,
                   labels(m) as source_labels,
                   m as source_node,
                   'incoming' as direction
            """
        else:
            query = f"""
            MATCH (n:{label})<-[r]-(m)
            WHERE any(prop IN keys(n) WHERE toString(n[prop]) = $node_id)
            RETURN type(r) as rel_type,
                   labels(m) as source_labels,
                   m as source_node,
                   'incoming' as direction
            LIMIT 1000
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

        # Get properties for each label (for LLM context)
        properties_by_label = {}
        for label in labels:
            props = self.get_node_properties(label)
            properties_by_label[label] = sorted(props.keys())

        schema = {
            'labels': labels,
            'product_types': products,
            'supporting_entities': supporting,
            'relationships': relationships,
            'relationship_types': [r['type'] for r in relationships],
            'properties': properties_by_label,
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
