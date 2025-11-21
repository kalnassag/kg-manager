"""
Localization Utilities

This module provides utilities for handling multilingual property labels,
including caching, fallback logic, and helper functions.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from .locales import normalize_locale, DEFAULT_LOCALE


# Configure logging
logger = logging.getLogger(__name__)


class TranslationCache:
    """
    In-memory cache for translation data with TTL support.

    This cache stores schema translations per locale to avoid repeated database queries.
    Cache entries expire after a configurable TTL (default: 1 hour).
    """

    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize the translation cache.

        Args:
            ttl_minutes: Time-to-live for cache entries in minutes
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._ttl = timedelta(minutes=ttl_minutes)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from cache if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            return None

        # Check if entry has expired
        if datetime.now() - self._timestamps[key] > self._ttl:
            logger.debug(f"Cache entry expired: {key}")
            self.invalidate(key)
            return None

        logger.debug(f"Cache hit: {key}")
        return self._cache[key]

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set a value in cache with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        logger.debug(f"Cache set: {key}")

    def invalidate(self, key: str) -> None:
        """
        Remove a specific key from cache.

        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            logger.debug(f"Cache invalidated: {key}")

    def invalidate_all(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("All cache entries invalidated")

    def invalidate_locale(self, locale: str) -> None:
        """
        Invalidate all cache entries for a specific locale.

        Args:
            locale: Locale code to invalidate
        """
        keys_to_remove = [k for k in self._cache.keys() if f":{locale}" in k]
        for key in keys_to_remove:
            self.invalidate(key)
        logger.info(f"Invalidated cache for locale: {locale}")

    def invalidate_entity_type(self, entity_type: str) -> None:
        """
        Invalidate all cache entries for a specific entity type.

        Args:
            entity_type: Entity type to invalidate (e.g., 'Laptop')
        """
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"schema:{entity_type}:")]
        for key in keys_to_remove:
            self.invalidate(key)
        logger.info(f"Invalidated cache for entity type: {entity_type}")

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache size and entry count
        """
        return {
            'entry_count': len(self._cache),
            'timestamp_count': len(self._timestamps)
        }


# Global translation cache instance
_translation_cache = TranslationCache(ttl_minutes=60)


def get_translation_cache() -> TranslationCache:
    """
    Get the global translation cache instance.

    Returns:
        Global TranslationCache instance
    """
    return _translation_cache


def get_schema_cache_key(entity_type: str, locale: str) -> str:
    """
    Generate cache key for schema translations.

    Args:
        entity_type: Entity type (e.g., 'Laptop')
        locale: Locale code (e.g., 'es-ES')

    Returns:
        Cache key string
    """
    return f"schema:{entity_type}:{locale}"


def get_coverage_cache_key(entity_type: str) -> str:
    """
    Generate cache key for translation coverage reports.

    Args:
        entity_type: Entity type (e.g., 'Laptop')

    Returns:
        Cache key string
    """
    return f"coverage:{entity_type}"


def apply_translation_fallback(
    property_key: str,
    translation: Optional[str],
    locale: str
) -> str:
    """
    Apply fallback logic for property translations.

    Fallback order:
    1. Use translation if available
    2. Use technical property key as fallback
    3. Log missing translation for tracking

    Args:
        property_key: Technical property key (e.g., 'design_body_weight_g')
        translation: Translated label (can be None)
        locale: Requested locale

    Returns:
        Display label (either translation or property key)
    """
    if translation:
        return translation

    # Log missing translation for future addition
    if locale != DEFAULT_LOCALE:
        logger.warning(
            f"Missing translation for property '{property_key}' in locale '{locale}'. "
            f"Using technical key as fallback."
        )

    return property_key


def humanize_property_key(property_key: str) -> str:
    """
    Convert a technical property key to a human-readable label.

    This is used as a last-resort fallback when no translation is available.

    Args:
        property_key: Technical property key (e.g., 'design_body_weight_g')

    Returns:
        Humanized label (e.g., 'Design Body Weight G')

    Examples:
        >>> humanize_property_key('design_body_weight_g')
        'Design Body Weight G'
        >>> humanize_property_key('inside_ram_capacity')
        'Inside RAM Capacity'
    """
    # Replace underscores with spaces
    parts = property_key.split('_')

    # Capitalize each part
    humanized_parts = [part.upper() if len(part) <= 3 else part.capitalize() for part in parts]

    return ' '.join(humanized_parts)


def format_property_value(value: Any, data_type: Optional[str] = None) -> str:
    """
    Format a property value for display.

    Args:
        value: Property value (can be any type)
        data_type: Data type hint (e.g., 'INTEGER', 'BOOLEAN', 'STRING')

    Returns:
        Formatted string representation of the value
    """
    if value is None:
        return ''

    # Handle boolean values
    if data_type == 'BOOLEAN' or isinstance(value, bool):
        return 'Yes' if value else 'No'

    # Handle numeric values
    if data_type in ('INTEGER', 'FLOAT') or isinstance(value, (int, float)):
        return str(value)

    # Handle lists/arrays
    if isinstance(value, list):
        return ', '.join(str(v) for v in value)

    # Default: convert to string
    return str(value)


def build_localized_response(
    data: Dict[str, Any],
    locale: str,
    entity_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build a standardized localized API response.

    Args:
        data: Response data
        locale: Locale used for the response
        entity_type: Optional entity type

    Returns:
        Response dictionary with locale metadata
    """
    response = {
        'locale': locale,
        **data
    }

    if entity_type:
        response['entity_type'] = entity_type

    return response


def get_missing_translations(
    available_locales: List[str],
    expected_locales: List[str]
) -> List[str]:
    """
    Get list of missing translations.

    Args:
        available_locales: List of locales that have translations
        expected_locales: List of expected/supported locales

    Returns:
        List of missing locale codes
    """
    return [locale for locale in expected_locales if locale not in available_locales]
