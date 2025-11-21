"""
Property Schema Management Queries

This module provides Neo4j queries for managing PropertyDefinition and PropertyLabel nodes
in the knowledge graph. These nodes form the multilingual metadata layer for property translations.
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from .connection import Neo4jConnection, get_connection


# Configure logging
logger = logging.getLogger(__name__)


class PropertySchemaQueries:
    """
    Handles all database queries for property schema management.

    This class manages CRUD operations for PropertyDefinition and PropertyLabel nodes,
    translation management, and property discovery from actual data.
    """

    def __init__(self):
        """Initialize property schema queries."""
        self.connection = get_connection()

    # ============================================================================
    # Property Definition CRUD
    # ============================================================================

    def get_all_properties(
        self,
        entity_type: Optional[str] = None,
        translation_status: Optional[str] = None,
        search_term: Optional[str] = None,
        expected_locale_count: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Get all property definitions with translation status.

        Args:
            entity_type: Filter by entity type (e.g., 'Laptop')
            translation_status: Filter by status ('complete', 'incomplete', 'none')
            search_term: Search in property key or translation labels
            expected_locale_count: Number of expected translations

        Returns:
            List of property definitions with metadata
        """
        query = """
        MATCH (pd:PropertyDefinition)
        """

        # Add entity type filter
        if entity_type:
            query += "WHERE pd.entity_type = $entity_type\n"

        query += """
        OPTIONAL MATCH (pd)-[:HAS_LABEL]->(pl:PropertyLabel)

        WITH pd, collect(DISTINCT {locale: pl.locale, label: pl.label}) as translations

        WITH pd, translations,
             size([t IN translations WHERE t.locale IS NOT NULL]) as translation_count
        """

        # Add search filter
        if search_term:
            query += """
            WHERE pd.property_key CONTAINS $search_term
               OR any(t IN translations WHERE t.label CONTAINS $search_term)
            """

        # Add translation status filter
        if translation_status == 'complete':
            query += "WHERE translation_count = $expected_locale_count\n"
        elif translation_status == 'incomplete':
            query += "WHERE translation_count > 0 AND translation_count < $expected_locale_count\n"
        elif translation_status == 'none':
            query += "WHERE translation_count = 0\n"

        query += """
        RETURN pd.property_key as property_key,
               pd.entity_type as entity_type,
               pd.data_type as data_type,
               pd.unit as unit,
               translations,
               translation_count,
               CASE
                 WHEN translation_count = $expected_locale_count THEN 'complete'
                 WHEN translation_count > 0 THEN 'incomplete'
                 ELSE 'none'
               END as status
        ORDER BY pd.entity_type, pd.property_key
        """

        params = {
            'expected_locale_count': expected_locale_count
        }

        if entity_type:
            params['entity_type'] = entity_type
        if search_term:
            params['search_term'] = search_term

        try:
            results = self.connection.execute_query(query, params)
            logger.info(f"Retrieved {len(results)} properties")
            return results
        except Exception as e:
            logger.error(f"Error getting properties: {e}")
            raise

    def get_property(self, property_key: str, entity_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a single property definition with all translations.

        Args:
            property_key: Property key (e.g., 'design_body_weight_g')
            entity_type: Entity type (e.g., 'Laptop')

        Returns:
            Property definition with translations, or None if not found
        """
        query = """
        MATCH (pd:PropertyDefinition {property_key: $property_key, entity_type: $entity_type})
        OPTIONAL MATCH (pd)-[:HAS_LABEL]->(pl:PropertyLabel)

        WITH pd, collect({locale: pl.locale, label: pl.label}) as translations

        RETURN pd.property_key as property_key,
               pd.entity_type as entity_type,
               pd.data_type as data_type,
               pd.unit as unit,
               translations
        """

        params = {
            'property_key': property_key,
            'entity_type': entity_type
        }

        try:
            results = self.connection.execute_query(query, params)
            if results:
                return results[0]
            return None
        except Exception as e:
            logger.error(f"Error getting property {property_key}/{entity_type}: {e}")
            raise

    def create_property(
        self,
        property_key: str,
        entity_type: str,
        data_type: str,
        unit: Optional[str] = None,
        translations: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new property definition with optional translations.

        Args:
            property_key: Property key
            entity_type: Entity type
            data_type: Data type (STRING, INTEGER, FLOAT, BOOLEAN)
            unit: Unit of measurement (optional)
            translations: Dict of locale -> label (optional)

        Returns:
            Created property definition
        """
        query = """
        CREATE (pd:PropertyDefinition {
            property_key: $property_key,
            entity_type: $entity_type,
            data_type: $data_type,
            unit: $unit
        })
        """

        if translations:
            query += """
            WITH pd
            UNWIND $translations as trans
            MERGE (pl:PropertyLabel {locale: trans.locale})
            SET pl.label = trans.label
            MERGE (pd)-[:HAS_LABEL]->(pl)
            """

        query += """
        RETURN pd.property_key as property_key,
               pd.entity_type as entity_type,
               pd.data_type as data_type,
               pd.unit as unit
        """

        params = {
            'property_key': property_key,
            'entity_type': entity_type,
            'data_type': data_type,
            'unit': unit
        }

        if translations:
            trans_list = [{'locale': k, 'label': v} for k, v in translations.items() if v]
            params['translations'] = trans_list

        try:
            results = self.connection.execute_query(query, params)
            logger.info(f"Created property {property_key}/{entity_type}")
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Error creating property: {e}")
            raise

    def update_property(
        self,
        property_key: str,
        entity_type: str,
        data_type: Optional[str] = None,
        unit: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update property definition metadata (not translations).

        Args:
            property_key: Property key
            entity_type: Entity type
            data_type: New data type (optional)
            unit: New unit (optional)

        Returns:
            Updated property definition
        """
        set_clauses = []
        params = {
            'property_key': property_key,
            'entity_type': entity_type
        }

        if data_type is not None:
            set_clauses.append("pd.data_type = $data_type")
            params['data_type'] = data_type

        if unit is not None:
            set_clauses.append("pd.unit = $unit")
            params['unit'] = unit

        if not set_clauses:
            # Nothing to update
            return self.get_property(property_key, entity_type)

        query = f"""
        MATCH (pd:PropertyDefinition {{property_key: $property_key, entity_type: $entity_type}})
        SET {', '.join(set_clauses)}
        RETURN pd.property_key as property_key,
               pd.entity_type as entity_type,
               pd.data_type as data_type,
               pd.unit as unit
        """

        try:
            results = self.connection.execute_query(query, params)
            logger.info(f"Updated property {property_key}/{entity_type}")
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Error updating property: {e}")
            raise

    def delete_property(self, property_key: str, entity_type: str) -> bool:
        """
        Delete a property definition and its HAS_LABEL relationships.

        Note: PropertyLabel nodes are not deleted as they might be shared.

        Args:
            property_key: Property key
            entity_type: Entity type

        Returns:
            True if deleted, False if not found
        """
        query = """
        MATCH (pd:PropertyDefinition {property_key: $property_key, entity_type: $entity_type})
        OPTIONAL MATCH (pd)-[r:HAS_LABEL]->()
        DELETE r, pd
        RETURN count(pd) as deleted_count
        """

        params = {
            'property_key': property_key,
            'entity_type': entity_type
        }

        try:
            results = self.connection.execute_query(query, params)
            deleted = results[0]['deleted_count'] > 0 if results else False

            if deleted:
                logger.info(f"Deleted property {property_key}/{entity_type}")
            else:
                logger.warning(f"Property not found: {property_key}/{entity_type}")

            return deleted
        except Exception as e:
            logger.error(f"Error deleting property: {e}")
            raise

    # ============================================================================
    # Translation Management
    # ============================================================================

    def set_translation(
        self,
        property_key: str,
        entity_type: str,
        locale: str,
        label: str
    ) -> Dict[str, Any]:
        """
        Add or update a translation for a property.

        Args:
            property_key: Property key
            entity_type: Entity type
            locale: Locale code (e.g., 'es-ES')
            label: Translated label

        Returns:
            Translation info
        """
        query = """
        MATCH (pd:PropertyDefinition {property_key: $property_key, entity_type: $entity_type})
        MERGE (pl:PropertyLabel {locale: $locale})
        SET pl.label = $label
        MERGE (pd)-[:HAS_LABEL]->(pl)
        RETURN pl.locale as locale, pl.label as label
        """

        params = {
            'property_key': property_key,
            'entity_type': entity_type,
            'locale': locale,
            'label': label
        }

        try:
            results = self.connection.execute_query(query, params)
            logger.info(f"Set translation for {property_key}/{entity_type} in {locale}")
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Error setting translation: {e}")
            raise

    def set_translations_bulk(
        self,
        property_key: str,
        entity_type: str,
        translations: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Set multiple translations for a property at once.

        Args:
            property_key: Property key
            entity_type: Entity type
            translations: Dict of locale -> label

        Returns:
            List of set translations
        """
        query = """
        MATCH (pd:PropertyDefinition {property_key: $property_key, entity_type: $entity_type})

        WITH pd
        UNWIND $translations as trans
        MERGE (pl:PropertyLabel {locale: trans.locale})
        SET pl.label = trans.label
        MERGE (pd)-[:HAS_LABEL]->(pl)

        RETURN pl.locale as locale, pl.label as label
        """

        trans_list = [{'locale': k, 'label': v} for k, v in translations.items() if v]

        params = {
            'property_key': property_key,
            'entity_type': entity_type,
            'translations': trans_list
        }

        try:
            results = self.connection.execute_query(query, params)
            logger.info(f"Set {len(results)} translations for {property_key}/{entity_type}")
            return results
        except Exception as e:
            logger.error(f"Error setting bulk translations: {e}")
            raise

    def delete_translation(
        self,
        property_key: str,
        entity_type: str,
        locale: str
    ) -> bool:
        """
        Remove a translation for a property.

        Args:
            property_key: Property key
            entity_type: Entity type
            locale: Locale to remove

        Returns:
            True if deleted, False if not found
        """
        query = """
        MATCH (pd:PropertyDefinition {property_key: $property_key, entity_type: $entity_type})
              -[r:HAS_LABEL]->(pl:PropertyLabel {locale: $locale})
        DELETE r
        RETURN count(r) as deleted_count
        """

        params = {
            'property_key': property_key,
            'entity_type': entity_type,
            'locale': locale
        }

        try:
            results = self.connection.execute_query(query, params)
            deleted = results[0]['deleted_count'] > 0 if results else False

            if deleted:
                logger.info(f"Deleted translation for {property_key}/{entity_type} in {locale}")

            return deleted
        except Exception as e:
            logger.error(f"Error deleting translation: {e}")
            raise

    # ============================================================================
    # Property Discovery
    # ============================================================================

    def discover_undocumented_properties(
        self,
        entity_type: str,
        sample_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find properties that exist in actual data but don't have PropertyDefinition.

        Args:
            entity_type: Entity type to scan (e.g., 'Laptop')
            sample_size: Number of nodes to sample

        Returns:
            List of undocumented properties with sample values
        """
        query = f"""
        // Get sample of nodes
        MATCH (n:{entity_type})
        WITH n LIMIT $sample_size

        // Get all property keys
        WITH collect(keys(n)) as all_keys_list
        UNWIND all_keys_list as keys_array
        UNWIND keys_array as prop_key

        // Get distinct keys with whether they're documented
        WITH DISTINCT prop_key
        OPTIONAL MATCH (pd:PropertyDefinition {{property_key: prop_key, entity_type: $entity_type}})

        // Only return undocumented ones
        WHERE pd IS NULL

        // Get sample values for type inference
        MATCH (n:{entity_type})
        WHERE n[prop_key] IS NOT NULL
        WITH prop_key, collect(DISTINCT n[prop_key])[0..5] as sample_values

        RETURN prop_key,
               sample_values,
               CASE
                 WHEN all(v IN sample_values WHERE v =~ '^[0-9]+$') THEN 'INTEGER'
                 WHEN all(v IN sample_values WHERE v =~ '^[0-9]+\\.[0-9]+$') THEN 'FLOAT'
                 WHEN all(v IN sample_values WHERE v IN [true, false, 'true', 'false']) THEN 'BOOLEAN'
                 ELSE 'STRING'
               END as suggested_type
        ORDER BY prop_key
        """

        params = {
            'entity_type': entity_type,
            'sample_size': sample_size
        }

        try:
            results = self.connection.execute_query(query, params)
            logger.info(f"Discovered {len(results)} undocumented properties for {entity_type}")
            return results
        except Exception as e:
            logger.error(f"Error discovering properties: {e}")
            raise

    # ============================================================================
    # Statistics and Reporting
    # ============================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about property definitions and translations.

        Returns:
            Dictionary with various statistics
        """
        query = """
        // Get counts per entity type
        MATCH (pd:PropertyDefinition)
        OPTIONAL MATCH (pd)-[:HAS_LABEL]->(pl:PropertyLabel)

        WITH pd.entity_type as entity_type,
             count(DISTINCT pd) as total_properties,
             count(DISTINCT pl) as total_translations

        RETURN entity_type,
               total_properties,
               total_translations
        ORDER BY entity_type
        """

        try:
            results = self.connection.execute_query(query)

            # Calculate totals
            total_props = sum(r['total_properties'] for r in results)
            total_trans = sum(r['total_translations'] for r in results)

            return {
                'by_entity_type': results,
                'total_properties': total_props,
                'total_translations': total_trans
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise

    def get_coverage_report(
        self,
        entity_type: Optional[str] = None,
        expected_locales: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get translation coverage report for properties.

        Args:
            entity_type: Filter by entity type (optional)
            expected_locales: List of expected locale codes

        Returns:
            List of properties with their translation coverage
        """
        if expected_locales is None:
            expected_locales = ['ar', 'de', 'es-ES', 'fr', 'pt-BR', 'zh-CN']

        query = """
        MATCH (pd:PropertyDefinition)
        """

        if entity_type:
            query += "WHERE pd.entity_type = $entity_type\n"

        query += """
        OPTIONAL MATCH (pd)-[:HAS_LABEL]->(pl:PropertyLabel)

        WITH pd, collect(DISTINCT pl.locale) as available_locales

        RETURN pd.property_key as property_key,
               pd.entity_type as entity_type,
               available_locales,
               [locale IN $expected_locales WHERE NOT locale IN available_locales] as missing_locales,
               size(available_locales) as coverage_count,
               size($expected_locales) as total_locales,
               100.0 * size(available_locales) / size($expected_locales) as coverage_percentage
        ORDER BY coverage_percentage ASC, pd.entity_type, pd.property_key
        """

        params = {
            'expected_locales': expected_locales
        }

        if entity_type:
            params['entity_type'] = entity_type

        try:
            results = self.connection.execute_query(query, params)
            logger.info(f"Generated coverage report with {len(results)} properties")
            return results
        except Exception as e:
            logger.error(f"Error getting coverage report: {e}")
            raise

    def get_entity_types(self) -> List[Dict[str, Any]]:
        """
        Get list of entity types that have PropertyDefinitions.

        Returns:
            List of dictionaries with entity_type and property_count
        """
        query = """
        MATCH (pd:PropertyDefinition)
        WITH pd.entity_type as entity_type, count(pd) as property_count
        RETURN entity_type, property_count
        ORDER BY entity_type
        """

        try:
            results = self.connection.execute_query(query)
            entity_types = [
                {
                    'entity_type': r['entity_type'],
                    'property_count': r['property_count']
                }
                for r in results
            ]
            return entity_types
        except Exception as e:
            logger.error(f"Error getting entity types: {e}")
            raise


# Singleton instance
_property_schema_queries: Optional[PropertySchemaQueries] = None


def get_property_schema_queries() -> PropertySchemaQueries:
    """
    Get or create the global PropertySchemaQueries instance.

    Returns:
        Global PropertySchemaQueries instance
    """
    global _property_schema_queries

    if _property_schema_queries is None:
        _property_schema_queries = PropertySchemaQueries()

    return _property_schema_queries
