"""
Tests for localization utilities.

Tests the localization utilities including caching, fallback logic,
and helper functions.
"""

import pytest
from datetime import datetime, timedelta
from backend.utils.localization import (
    TranslationCache,
    get_schema_cache_key,
    get_coverage_cache_key,
    apply_translation_fallback,
    humanize_property_key,
    format_property_value,
    get_missing_translations
)


class TestTranslationCache:
    """Test translation cache functionality."""

    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        cache = TranslationCache(ttl_minutes=60)
        test_data = {'test': 'data'}

        cache.set('test_key', test_data)
        result = cache.get('test_key')

        assert result == test_data

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = TranslationCache(ttl_minutes=60)
        result = cache.get('nonexistent_key')
        assert result is None

    def test_cache_invalidate(self):
        """Test cache invalidation."""
        cache = TranslationCache(ttl_minutes=60)
        cache.set('test_key', {'test': 'data'})

        cache.invalidate('test_key')
        result = cache.get('test_key')

        assert result is None

    def test_cache_invalidate_all(self):
        """Test invalidating all cache entries."""
        cache = TranslationCache(ttl_minutes=60)
        cache.set('key1', {'data': '1'})
        cache.set('key2', {'data': '2'})

        cache.invalidate_all()

        assert cache.get('key1') is None
        assert cache.get('key2') is None

    def test_cache_invalidate_locale(self):
        """Test invalidating cache entries for a specific locale."""
        cache = TranslationCache(ttl_minutes=60)
        cache.set('schema:Laptop:es-ES', {'data': 'es'})
        cache.set('schema:Laptop:fr', {'data': 'fr'})

        cache.invalidate_locale('es-ES')

        assert cache.get('schema:Laptop:es-ES') is None
        assert cache.get('schema:Laptop:fr') is not None

    def test_cache_invalidate_entity_type(self):
        """Test invalidating cache entries for a specific entity type."""
        cache = TranslationCache(ttl_minutes=60)
        cache.set('schema:Laptop:es-ES', {'data': 'laptop'})
        cache.set('schema:Smartphone:es-ES', {'data': 'phone'})

        cache.invalidate_entity_type('Laptop')

        assert cache.get('schema:Laptop:es-ES') is None
        assert cache.get('schema:Smartphone:es-ES') is not None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = TranslationCache(ttl_minutes=60)
        cache.set('key1', {'data': '1'})
        cache.set('key2', {'data': '2'})

        stats = cache.get_stats()

        assert stats['entry_count'] == 2
        assert stats['timestamp_count'] == 2


class TestCacheKeyGeneration:
    """Test cache key generation functions."""

    def test_schema_cache_key(self):
        """Test schema cache key generation."""
        key = get_schema_cache_key('Laptop', 'es-ES')
        assert key == 'schema:Laptop:es-ES'

    def test_coverage_cache_key(self):
        """Test coverage cache key generation."""
        key = get_coverage_cache_key('Laptop')
        assert key == 'coverage:Laptop'


class TestTranslationFallback:
    """Test translation fallback logic."""

    def test_fallback_with_translation(self):
        """Test fallback when translation is available."""
        result = apply_translation_fallback(
            'design_body_weight_g',
            'Peso del cuerpo',
            'es-ES'
        )
        assert result == 'Peso del cuerpo'

    def test_fallback_without_translation(self):
        """Test fallback when translation is missing."""
        result = apply_translation_fallback(
            'design_body_weight_g',
            None,
            'es-ES'
        )
        assert result == 'design_body_weight_g'

    def test_fallback_default_locale(self):
        """Test fallback for default locale doesn't log warning."""
        result = apply_translation_fallback(
            'design_body_weight_g',
            None,
            'en'
        )
        assert result == 'design_body_weight_g'


class TestPropertyKeyHumanization:
    """Test property key humanization."""

    def test_humanize_simple_property(self):
        """Test humanizing a simple property key."""
        result = humanize_property_key('product_model')
        assert result == 'Product Model'

    def test_humanize_complex_property(self):
        """Test humanizing a complex property key."""
        result = humanize_property_key('design_body_weight_g')
        assert result == 'Design Body Weight G'

    def test_humanize_property_with_abbreviation(self):
        """Test humanizing property with abbreviation."""
        result = humanize_property_key('inside_ram_capacity')
        assert result == 'Inside RAM Capacity'

    def test_humanize_property_with_ssd(self):
        """Test humanizing property with SSD abbreviation."""
        result = humanize_property_key('inside_ssd_total_ssd_capacity')
        # SSD should be uppercase as it's <= 3 characters
        assert 'SSD' in result


class TestPropertyValueFormatting:
    """Test property value formatting."""

    def test_format_boolean_true(self):
        """Test formatting boolean true value."""
        result = format_property_value(True, 'BOOLEAN')
        assert result == 'Yes'

    def test_format_boolean_false(self):
        """Test formatting boolean false value."""
        result = format_property_value(False, 'BOOLEAN')
        assert result == 'No'

    def test_format_integer(self):
        """Test formatting integer value."""
        result = format_property_value(1500, 'INTEGER')
        assert result == '1500'

    def test_format_float(self):
        """Test formatting float value."""
        result = format_property_value(15.7, 'FLOAT')
        assert result == '15.7'

    def test_format_string(self):
        """Test formatting string value."""
        result = format_property_value('Test String', 'STRING')
        assert result == 'Test String'

    def test_format_list(self):
        """Test formatting list value."""
        result = format_property_value(['WiFi 5', 'WiFi 6'], 'ARRAY')
        assert result == 'WiFi 5, WiFi 6'

    def test_format_none(self):
        """Test formatting None value."""
        result = format_property_value(None)
        assert result == ''


class TestMissingTranslations:
    """Test missing translations detection."""

    def test_no_missing_translations(self):
        """Test when no translations are missing."""
        available = ['es-ES', 'fr', 'de', 'ar', 'pt-BR', 'zh-CN']
        expected = ['es-ES', 'fr', 'de', 'ar', 'pt-BR', 'zh-CN']

        missing = get_missing_translations(available, expected)
        assert missing == []

    def test_some_missing_translations(self):
        """Test when some translations are missing."""
        available = ['es-ES', 'fr']
        expected = ['es-ES', 'fr', 'de', 'ar', 'pt-BR', 'zh-CN']

        missing = get_missing_translations(available, expected)
        assert set(missing) == {'de', 'ar', 'pt-BR', 'zh-CN'}

    def test_all_missing_translations(self):
        """Test when all translations are missing."""
        available = []
        expected = ['es-ES', 'fr', 'de']

        missing = get_missing_translations(available, expected)
        assert set(missing) == {'es-ES', 'fr', 'de'}
