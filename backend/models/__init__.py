"""
Models package for KG Manager application.

This package contains Pydantic models for API request/response validation.
"""

from .localization import (
    LocaleInfo,
    LocalesResponse,
    PropertyDefinition,
    SchemaResponse,
    LocalizedProperty,
    EntityResponse,
    PropertyCoverage,
    TranslationCoverageResponse,
    ErrorResponse
)

__all__ = [
    'LocaleInfo',
    'LocalesResponse',
    'PropertyDefinition',
    'SchemaResponse',
    'LocalizedProperty',
    'EntityResponse',
    'PropertyCoverage',
    'TranslationCoverageResponse',
    'ErrorResponse'
]
