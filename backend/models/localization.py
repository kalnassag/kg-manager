"""
Pydantic Models for Localization API

This module defines the request and response models for the multilingual
property schema API endpoints.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LocaleInfo(BaseModel):
    """Information about a supported locale"""
    code: str = Field(..., description="BCP 47 locale code (e.g., 'es-ES', 'fr')")
    name: str = Field(..., description="Human-readable locale name")
    rtl: bool = Field(..., description="Whether locale uses right-to-left text direction")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "es-ES",
                "name": "Spanish (Spain)",
                "rtl": False
            }
        }


class LocalesResponse(BaseModel):
    """Response model for GET /api/locales endpoint"""
    locales: List[LocaleInfo] = Field(..., description="List of supported locales")
    default_locale: str = Field(..., description="Default locale code")
    total_count: int = Field(..., description="Total number of supported locales")

    class Config:
        json_schema_extra = {
            "example": {
                "locales": [
                    {"code": "en", "name": "English", "rtl": False},
                    {"code": "es-ES", "name": "Spanish (Spain)", "rtl": False},
                    {"code": "fr", "name": "French", "rtl": False}
                ],
                "default_locale": "en",
                "total_count": 3
            }
        }


class PropertyDefinition(BaseModel):
    """Property definition with localized label"""
    key: str = Field(..., description="Technical property key")
    display_name: str = Field(..., description="Localized display name")
    data_type: Optional[str] = Field(None, description="Data type (INTEGER, STRING, BOOLEAN, etc.)")
    unit: Optional[str] = Field(None, description="Unit of measurement (g, mm, GB, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "key": "design_body_weight_g",
                "display_name": "Peso del cuerpo",
                "data_type": "INTEGER",
                "unit": "g"
            }
        }


class SchemaResponse(BaseModel):
    """Response model for GET /api/schema/:entityType endpoint"""
    entity_type: str = Field(..., description="Entity type (e.g., 'Laptop', 'Smartphone')")
    locale: str = Field(..., description="Locale code used for translations")
    properties: List[PropertyDefinition] = Field(..., description="List of property definitions")
    total_properties: int = Field(..., description="Total number of properties")

    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "Laptop",
                "locale": "es-ES",
                "properties": [
                    {
                        "key": "design_body_weight_g",
                        "display_name": "Peso del cuerpo",
                        "data_type": "INTEGER",
                        "unit": "g"
                    },
                    {
                        "key": "inside_ram_capacity",
                        "display_name": "Capacidad de RAM",
                        "data_type": "INTEGER",
                        "unit": "GB"
                    }
                ],
                "total_properties": 2
            }
        }


class LocalizedProperty(BaseModel):
    """A property with its localized name and value"""
    technical_key: str = Field(..., description="Technical property key")
    display_name: str = Field(..., description="Localized display name")
    value: Optional[str] = Field(None, description="Property value (stringified)")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    data_type: Optional[str] = Field(None, description="Data type")

    class Config:
        json_schema_extra = {
            "example": {
                "technical_key": "design_body_weight_g",
                "display_name": "Peso del cuerpo",
                "value": "1500",
                "unit": "g",
                "data_type": "INTEGER"
            }
        }


class EntityResponse(BaseModel):
    """Response model for GET /api/:entityType/:id endpoint with localized properties"""
    id: str = Field(..., description="Entity identifier")
    entity_type: str = Field(..., description="Entity type")
    locale: str = Field(..., description="Locale code used for translations")
    properties: List[LocalizedProperty] = Field(..., description="List of localized properties")
    total_properties: int = Field(..., description="Total number of properties")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ASUS Chromebook Flip C433TA-AJ0121",
                "entity_type": "Laptop",
                "locale": "es-ES",
                "properties": [
                    {
                        "technical_key": "design_body_weight_g",
                        "display_name": "Peso del cuerpo",
                        "value": "1500",
                        "unit": "g",
                        "data_type": "INTEGER"
                    },
                    {
                        "technical_key": "inside_ram_capacity",
                        "display_name": "Capacidad de RAM",
                        "value": "8",
                        "unit": "GB",
                        "data_type": "INTEGER"
                    }
                ],
                "total_properties": 2
            }
        }


class PropertyCoverage(BaseModel):
    """Translation coverage for a single property"""
    property: str = Field(..., description="Property key")
    available_locales: List[str] = Field(..., description="Locales with translations")
    missing_locales: List[str] = Field(..., description="Locales without translations")
    coverage_count: int = Field(..., description="Number of available translations")
    coverage_percentage: float = Field(..., description="Percentage of coverage")

    class Config:
        json_schema_extra = {
            "example": {
                "property": "design_body_weight_g",
                "available_locales": ["es-ES", "fr", "de"],
                "missing_locales": ["ar", "pt-BR", "zh-CN"],
                "coverage_count": 3,
                "coverage_percentage": 50.0
            }
        }


class TranslationCoverageResponse(BaseModel):
    """Response model for GET /api/translation-coverage/:entityType endpoint"""
    entity_type: str = Field(..., description="Entity type")
    expected_locales: List[str] = Field(..., description="Expected/supported locales")
    total_properties: int = Field(..., description="Total number of properties")
    properties: List[PropertyCoverage] = Field(..., description="Coverage per property")

    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "Laptop",
                "expected_locales": ["en", "es-ES", "fr", "de", "ar", "pt-BR", "zh-CN"],
                "total_properties": 10,
                "properties": [
                    {
                        "property": "design_body_weight_g",
                        "available_locales": ["es-ES", "fr", "de"],
                        "missing_locales": ["ar", "pt-BR", "zh-CN"],
                        "coverage_count": 3,
                        "coverage_percentage": 50.0
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Entity not found",
                "detail": "Laptop with id 'XYZ123' does not exist",
                "status_code": 404
            }
        }
