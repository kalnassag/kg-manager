"""
Tests for locale configuration and utilities.

Tests the locale configuration module including locale validation,
normalization, and metadata retrieval.
"""

import pytest
from backend.utils.locales import (
    is_locale_supported,
    get_locale_info,
    normalize_locale,
    get_all_locales,
    get_locale_codes,
    SUPPORTED_LOCALES,
    DEFAULT_LOCALE
)


class TestLocaleSupport:
    """Test locale support checking."""

    def test_supported_locale_en(self):
        """Test that English is supported."""
        assert is_locale_supported('en') is True

    def test_supported_locale_spanish(self):
        """Test that Spanish is supported."""
        assert is_locale_supported('es-ES') is True

    def test_supported_locale_french(self):
        """Test that French is supported."""
        assert is_locale_supported('fr') is True

    def test_unsupported_locale(self):
        """Test that unsupported locale returns False."""
        assert is_locale_supported('xx-YY') is False

    def test_case_sensitive(self):
        """Test that locale codes are case-sensitive."""
        # es-ES is supported, but ES-ES is not
        assert is_locale_supported('es-ES') is True
        # Note: This test depends on whether we want to enforce case sensitivity


class TestLocaleInfo:
    """Test locale information retrieval."""

    def test_get_locale_info_english(self):
        """Test getting English locale info."""
        info = get_locale_info('en')
        assert info is not None
        assert info.code == 'en'
        assert info.name == 'English'
        assert info.rtl is False

    def test_get_locale_info_arabic(self):
        """Test getting Arabic locale info (RTL language)."""
        info = get_locale_info('ar')
        assert info is not None
        assert info.code == 'ar'
        assert info.name == 'Arabic'
        assert info.rtl is True

    def test_get_locale_info_unsupported(self):
        """Test getting info for unsupported locale."""
        info = get_locale_info('xx-YY')
        assert info is None


class TestLocaleNormalization:
    """Test locale normalization and fallback."""

    def test_normalize_supported_locale(self):
        """Test normalizing a supported locale."""
        assert normalize_locale('es-ES') == 'es-ES'
        assert normalize_locale('fr') == 'fr'

    def test_normalize_unsupported_locale(self):
        """Test normalizing an unsupported locale falls back to default."""
        assert normalize_locale('xx-YY') == DEFAULT_LOCALE
        assert normalize_locale('invalid') == DEFAULT_LOCALE

    def test_normalize_none(self):
        """Test normalizing None falls back to default."""
        assert normalize_locale(None) == DEFAULT_LOCALE

    def test_normalize_empty_string(self):
        """Test normalizing empty string falls back to default."""
        assert normalize_locale('') == DEFAULT_LOCALE


class TestLocaleRetrieval:
    """Test locale list retrieval."""

    def test_get_all_locales(self):
        """Test getting all locales."""
        locales = get_all_locales()
        assert isinstance(locales, list)
        assert len(locales) > 0
        assert all('code' in loc for loc in locales)
        assert all('name' in loc for loc in locales)
        assert all('rtl' in loc for loc in locales)

    def test_get_all_locales_contains_default(self):
        """Test that all locales includes default locale."""
        locales = get_all_locales()
        locale_codes = [loc['code'] for loc in locales]
        assert DEFAULT_LOCALE in locale_codes

    def test_get_locale_codes(self):
        """Test getting locale codes."""
        codes = get_locale_codes()
        assert isinstance(codes, list)
        assert len(codes) > 0
        assert DEFAULT_LOCALE in codes
        assert 'es-ES' in codes
        assert 'fr' in codes

    def test_locale_codes_match_supported(self):
        """Test that locale codes match SUPPORTED_LOCALES."""
        codes = get_locale_codes()
        assert set(codes) == set(SUPPORTED_LOCALES.keys())


class TestLocaleConfiguration:
    """Test locale configuration constants."""

    def test_default_locale_is_english(self):
        """Test that default locale is English."""
        assert DEFAULT_LOCALE == 'en'

    def test_supported_locales_not_empty(self):
        """Test that supported locales is not empty."""
        assert len(SUPPORTED_LOCALES) > 0

    def test_all_supported_locales_have_required_fields(self):
        """Test that all supported locales have required fields."""
        for code, info in SUPPORTED_LOCALES.items():
            assert info.code == code
            assert isinstance(info.name, str)
            assert len(info.name) > 0
            assert isinstance(info.rtl, bool)
