"""
Localization Database Queries

This module provides Neo4j queries for multilingual property schema operations,
including schema retrieval, entity localization, and translation coverage reporting.
"""

from typing import Dict, List, Optional, Any
import logging

from .connection import Neo4jConnection
from ..utils.locales import get_locale_codes, DEFAULT_LOCALE, normalize_locale
from ..utils.localization import (
    get_translation_cache,
    get_schema_cache_key,
    get_coverage_cache_key,
    apply_translation_fallback,
    humanize_property_key
)


# Configure logging
logger = logging.getLogger(__name__)


class LocalizationQueries:
    """
    Handles all localization-related database queries for the knowledge graph.

    This class provides methods to:
    - Retrieve property schemas with localized labels
    - Get entities with localized property names
    - Generate translation coverage reports
    - Manage translation data
    """

    def __init__(self, connection: Neo4jConnection):
        """
        Initialize localization queries.

        Args:
            connection: Neo4j connection instance
        """
        self.connection = connection
        self.cache = get_translation_cache()

    def get_schema_for_locale(
        self,
        entity_type: str,
        locale: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get property schema for an entity type with localized labels.

        Args:
            entity_type: Entity type (e.g., 'Laptop', 'Smartphone')
            locale: Locale code (e.g., 'es-ES', 'fr')
            use_cache: Whether to use cached results

        Returns:
            Dictionary with entity_type, locale, and properties list

        Example response:
            {
                'entity_type': 'Laptop',
                'locale': 'es-ES',
                'properties': [
                    {
                        'key': 'design_body_weight_g',
                        'display_name': 'Peso del cuerpo',
                        'data_type': 'INTEGER',
                        'unit': 'g'
                    },
                    ...
                ]
            }
        """
        # Normalize locale
        normalized_locale = normalize_locale(locale)

        # Check cache
        cache_key = get_schema_cache_key(entity_type, normalized_locale)
        if use_cache:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        # Query database
        query = """
        MATCH (pd:PropertyDefinition {entity_type: $entity_type})
        OPTIONAL MATCH (pd)-[:HAS_LABEL]->(pl:PropertyLabel {locale: $locale})

        RETURN pd.property_key as key,
               pl.label as display_name,
               pd.data_type as data_type,
               pd.unit as unit
        ORDER BY COALESCE(pl.label, pd.property_key)
        """

        params = {
            'entity_type': entity_type,
            'locale': normalized_locale
        }

        try:
            results = self.connection.execute_query(query, params)

            # Process results and apply fallback logic
            properties = []
            for record in results:
                property_key = record['key']
                translation = record.get('display_name')

                # Apply fallback if translation is missing
                display_name = apply_translation_fallback(
                    property_key,
                    translation,
                    normalized_locale
                )

                properties.append({
                    'key': property_key,
                    'display_name': display_name,
                    'data_type': record.get('data_type'),
                    'unit': record.get('unit')
                })

            result = {
                'entity_type': entity_type,
                'locale': normalized_locale,
                'properties': properties
            }

            # Cache result
            if use_cache:
                self.cache.set(cache_key, result)

            logger.info(
                f"Retrieved schema for {entity_type} in locale {normalized_locale}: "
                f"{len(properties)} properties"
            )

            return result

        except Exception as e:
            logger.error(f"Error getting schema for locale: {e}")
            raise

    def get_entity_with_localized_properties(
        self,
        entity_type: str,
        entity_id: str,
        locale: str,
        id_property: str = 'product_model'
    ) -> Optional[Dict[str, Any]]:
        """
        Get an entity with localized property names.

        Args:
            entity_type: Entity type (e.g., 'Laptop')
            entity_id: Entity identifier value
            locale: Locale code (e.g., 'es-ES', 'fr')
            id_property: Property name used for entity identification

        Returns:
            Dictionary with localized entity data or None if not found

        Example response:
            {
                'id': 'ASUS Chromebook Flip C433TA-AJ0121',
                'entity_type': 'Laptop',
                'locale': 'es-ES',
                'properties': [
                    {
                        'technical_key': 'design_body_weight_g',
                        'display_name': 'Peso del cuerpo',
                        'value': '1500',
                        'unit': 'g'
                    },
                    ...
                ]
            }
        """
        # Normalize locale
        normalized_locale = normalize_locale(locale)

        # Build dynamic Cypher query
        # This query retrieves the entity and all its properties with translations
        query = f"""
        WITH $locale as locale, $entity_id as entity_id

        MATCH (e:{entity_type} {{{id_property}: entity_id}})

        // Get all property definitions for this entity type
        MATCH (pd:PropertyDefinition {{entity_type: $entity_type}})
        OPTIONAL MATCH (pd)-[:HAS_LABEL]->(pl:PropertyLabel {{locale: locale}})

        // Collect all properties with their metadata
        WITH e, locale,
             collect({{
               key: pd.property_key,
               label: pl.label,
               data_type: pd.data_type,
               unit: pd.unit
             }}) as property_definitions

        // Extract entity properties
        WITH e, locale, property_definitions, properties(e) as entity_props

        RETURN
            e['{id_property}'] as entity_id,
            property_definitions,
            entity_props
        """

        params = {
            'locale': normalized_locale,
            'entity_id': entity_id,
            'entity_type': entity_type
        }

        try:
            results = self.connection.execute_query(query, params)

            if not results:
                logger.warning(f"Entity not found: {entity_type} with {id_property}={entity_id}")
                return None

            record = results[0]
            property_definitions = record['property_definitions']
            entity_props = record['entity_props']

            # Build localized properties list
            properties = []
            for prop_def in property_definitions:
                property_key = prop_def['key']

                # Get value from entity properties
                value = entity_props.get(property_key)

                # Skip properties without values
                if value is None:
                    continue

                # Apply translation fallback
                display_name = apply_translation_fallback(
                    property_key,
                    prop_def.get('label'),
                    normalized_locale
                )

                properties.append({
                    'technical_key': property_key,
                    'display_name': display_name,
                    'value': str(value) if value is not None else None,
                    'unit': prop_def.get('unit'),
                    'data_type': prop_def.get('data_type')
                })

            result = {
                'id': entity_id,
                'entity_type': entity_type,
                'locale': normalized_locale,
                'properties': properties
            }

            logger.info(
                f"Retrieved entity {entity_type}/{entity_id} in locale {normalized_locale}: "
                f"{len(properties)} properties"
            )

            return result

        except Exception as e:
            logger.error(f"Error getting entity with localized properties: {e}")
            raise

    def get_translation_coverage(
        self,
        entity_type: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get translation coverage report for an entity type.

        Shows which properties have translations in which locales and identifies gaps.

        Args:
            entity_type: Entity type (e.g., 'Laptop')
            use_cache: Whether to use cached results

        Returns:
            Dictionary with coverage information for each property

        Example response:
            {
                'entity_type': 'Laptop',
                'expected_locales': ['en', 'es-ES', 'fr', 'de', ...],
                'properties': [
                    {
                        'property': 'design_body_weight_g',
                        'available_locales': ['es-ES', 'fr', 'de'],
                        'missing_locales': ['ar', 'pt-BR', 'zh-CN'],
                        'coverage_count': 3,
                        'coverage_percentage': 50.0
                    },
                    ...
                ]
            }
        """
        # Check cache
        cache_key = get_coverage_cache_key(entity_type)
        if use_cache:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        # Get expected locales
        expected_locales = get_locale_codes()

        # Query database
        query = """
        MATCH (pd:PropertyDefinition {entity_type: $entity_type})
        OPTIONAL MATCH (pd)-[:HAS_LABEL]->(pl:PropertyLabel)

        WITH pd.property_key as property,
             collect(DISTINCT pl.locale) as available_locales

        RETURN property,
               available_locales
        ORDER BY size(available_locales) ASC, property ASC
        """

        params = {
            'entity_type': entity_type
        }

        try:
            results = self.connection.execute_query(query, params)

            # Process results
            properties = []
            for record in results:
                property_key = record['property']
                available_locales = [loc for loc in record['available_locales'] if loc]  # Filter out None

                # Calculate missing locales
                missing_locales = [
                    locale for locale in expected_locales
                    if locale not in available_locales and locale != DEFAULT_LOCALE
                ]

                coverage_count = len(available_locales)
                total_locales = len(expected_locales) - 1  # Exclude default locale
                coverage_percentage = (coverage_count / total_locales * 100) if total_locales > 0 else 0

                properties.append({
                    'property': property_key,
                    'available_locales': sorted(available_locales),
                    'missing_locales': sorted(missing_locales),
                    'coverage_count': coverage_count,
                    'coverage_percentage': round(coverage_percentage, 1)
                })

            result = {
                'entity_type': entity_type,
                'expected_locales': expected_locales,
                'total_properties': len(properties),
                'properties': properties
            }

            # Cache result
            if use_cache:
                self.cache.set(cache_key, result)

            logger.info(
                f"Retrieved translation coverage for {entity_type}: "
                f"{len(properties)} properties"
            )

            return result

        except Exception as e:
            logger.error(f"Error getting translation coverage: {e}")
            raise

    def get_available_locales_for_entity_type(self, entity_type: str) -> List[str]:
        """
        Get list of locales that have at least one translation for an entity type.

        Args:
            entity_type: Entity type (e.g., 'Laptop')

        Returns:
            List of locale codes that have translations
        """
        query = """
        MATCH (pd:PropertyDefinition {entity_type: $entity_type})
              -[:HAS_LABEL]->(pl:PropertyLabel)
        RETURN DISTINCT pl.locale as locale
        ORDER BY locale
        """

        params = {'entity_type': entity_type}

        try:
            results = self.connection.execute_query(query, params)
            locales = [record['locale'] for record in results if record.get('locale')]

            logger.info(f"Found {len(locales)} locales with translations for {entity_type}")

            return locales

        except Exception as e:
            logger.error(f"Error getting available locales: {e}")
            raise

    def invalidate_cache_for_entity_type(self, entity_type: str) -> None:
        """
        Invalidate all cached data for a specific entity type.

        This should be called when translations are updated.

        Args:
            entity_type: Entity type to invalidate cache for
        """
        self.cache.invalidate_entity_type(entity_type)
        logger.info(f"Invalidated cache for entity type: {entity_type}")

    def invalidate_cache_for_locale(self, locale: str) -> None:
        """
        Invalidate all cached data for a specific locale.

        This should be called when translations are updated for a locale.

        Args:
            locale: Locale to invalidate cache for
        """
        self.cache.invalidate_locale(locale)
        logger.info(f"Invalidated cache for locale: {locale}")

    def invalidate_all_caches(self) -> None:
        """Invalidate all translation caches."""
        self.cache.invalidate_all()
        logger.info("Invalidated all translation caches")


# Singleton instance
_localization_queries: Optional[LocalizationQueries] = None


def get_localization_queries(connection: Neo4jConnection = None) -> LocalizationQueries:
    """
    Get or create the global LocalizationQueries instance.

    Args:
        connection: Neo4j connection (required on first call)

    Returns:
        Global LocalizationQueries instance
    """
    global _localization_queries

    if _localization_queries is None:
        if connection is None:
            raise ValueError("Connection required for first initialization")
        _localization_queries = LocalizationQueries(connection)

    return _localization_queries
