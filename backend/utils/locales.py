"""
Locale Configuration for Multilingual Support

This module defines supported locales and provides utilities for locale validation
and fallback behavior in the knowledge graph manager application.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class LocaleInfo:
    """Information about a supported locale"""
    code: str
    name: str
    rtl: bool  # Right-to-left text direction

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'code': self.code,
            'name': self.name,
            'rtl': self.rtl
        }


# Supported locales configuration
# Using BCP 47 language codes (e.g., 'es-ES', 'pt-BR')
SUPPORTED_LOCALES: Dict[str, LocaleInfo] = {
    'en': LocaleInfo(code='en', name='English', rtl=False),
    'ar': LocaleInfo(code='ar', name='Arabic', rtl=True),
    'de': LocaleInfo(code='de', name='German', rtl=False),
    'es-ES': LocaleInfo(code='es-ES', name='Spanish (Spain)', rtl=False),
    'fr': LocaleInfo(code='fr', name='French', rtl=False),
    'pt-BR': LocaleInfo(code='pt-BR', name='Portuguese (Brazil)', rtl=False),
    'zh-CN': LocaleInfo(code='zh-CN', name='Chinese (Simplified)', rtl=False),
}

# Default locale to use when requested locale is not available
DEFAULT_LOCALE = 'en'


def is_locale_supported(locale: str) -> bool:
    """
    Check if a locale is supported.

    Args:
        locale: Locale code to check (e.g., 'es-ES', 'fr')

    Returns:
        True if locale is supported, False otherwise
    """
    return locale in SUPPORTED_LOCALES


def get_locale_info(locale: str) -> Optional[LocaleInfo]:
    """
    Get information about a locale.

    Args:
        locale: Locale code (e.g., 'es-ES', 'fr')

    Returns:
        LocaleInfo object if locale is supported, None otherwise
    """
    return SUPPORTED_LOCALES.get(locale)


def normalize_locale(locale: Optional[str]) -> str:
    """
    Normalize and validate a locale code.
    Falls back to DEFAULT_LOCALE if the provided locale is not supported.

    Args:
        locale: Locale code to normalize (can be None)

    Returns:
        Normalized locale code (guaranteed to be supported)

    Examples:
        >>> normalize_locale('es-ES')
        'es-ES'
        >>> normalize_locale('xx-YY')  # Unsupported locale
        'en'
        >>> normalize_locale(None)
        'en'
    """
    if locale is None:
        return DEFAULT_LOCALE

    # Check if locale is supported
    if is_locale_supported(locale):
        return locale

    # Fallback to default
    return DEFAULT_LOCALE


def get_all_locales() -> List[Dict]:
    """
    Get list of all supported locales.

    Returns:
        List of locale dictionaries with code, name, and rtl fields
    """
    return [locale_info.to_dict() for locale_info in SUPPORTED_LOCALES.values()]


def get_locale_codes() -> List[str]:
    """
    Get list of all supported locale codes.

    Returns:
        List of locale codes (e.g., ['en', 'es-ES', 'fr', ...])
    """
    return list(SUPPORTED_LOCALES.keys())
