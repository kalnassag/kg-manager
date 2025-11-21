"""Pydantic models for Property Schema API endpoints."""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class PropertyTranslation(BaseModel):
    """Model for a single property translation."""
    locale: str = Field(..., description="Locale code (e.g., 'en', 'es-ES')")
    label: str = Field(..., description="Translated label")

    class Config:
        schema_extra = {
            "example": {
                "locale": "es-ES",
                "label": "Precio"
            }
        }


class PropertyDefinitionBase(BaseModel):
    """Base model for property definition."""
    property_key: str = Field(..., description="Technical property key (e.g., 'price', 'screen_size')")
    entity_type: str = Field(..., description="Entity type this property belongs to (e.g., 'Laptop', 'Smartphone')")
    data_type: str = Field(default="STRING", description="Data type: STRING, INTEGER, FLOAT, BOOLEAN, DATE, ARRAY")
    unit: Optional[str] = Field(default=None, description="Unit of measurement (e.g., 'USD', 'inches', 'GB')")

    @validator('data_type')
    def validate_data_type(cls, v):
        allowed_types = ['STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'DATE', 'ARRAY']
        if v not in allowed_types:
            raise ValueError(f'data_type must be one of {allowed_types}')
        return v

    @validator('property_key')
    def validate_property_key(cls, v):
        # Property key should be lowercase with underscores
        if not v.replace('_', '').isalnum():
            raise ValueError('property_key must contain only alphanumeric characters and underscores')
        return v.lower()


class CreatePropertyRequest(PropertyDefinitionBase):
    """Request model for creating a property definition."""
    translations: Optional[List[PropertyTranslation]] = Field(default=None, description="Optional initial translations")

    class Config:
        schema_extra = {
            "example": {
                "property_key": "price",
                "entity_type": "Laptop",
                "data_type": "FLOAT",
                "unit": "USD",
                "translations": [
                    {"locale": "en", "label": "Price"},
                    {"locale": "es-ES", "label": "Precio"}
                ]
            }
        }


class UpdatePropertyRequest(BaseModel):
    """Request model for updating a property definition."""
    data_type: Optional[str] = Field(default=None, description="Data type")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")

    @validator('data_type')
    def validate_data_type(cls, v):
        if v is not None:
            allowed_types = ['STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'DATE', 'ARRAY']
            if v not in allowed_types:
                raise ValueError(f'data_type must be one of {allowed_types}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "data_type": "INTEGER",
                "unit": "GB"
            }
        }


class SetTranslationRequest(BaseModel):
    """Request model for setting a single translation."""
    label: str = Field(..., description="Translated label")

    class Config:
        schema_extra = {
            "example": {
                "label": "Tamaño de Pantalla"
            }
        }


class BulkTranslationsRequest(BaseModel):
    """Request model for bulk updating translations."""
    translations: Dict[str, str] = Field(..., description="Map of locale -> label")

    class Config:
        schema_extra = {
            "example": {
                "translations": {
                    "en": "Screen Size",
                    "es-ES": "Tamaño de Pantalla",
                    "fr": "Taille d'Écran"
                }
            }
        }


class PropertyDefinitionResponse(PropertyDefinitionBase):
    """Response model for a property definition with all translations."""
    translations: List[PropertyTranslation] = Field(default=[], description="All translations")
    translation_count: int = Field(default=0, description="Number of available translations")

    class Config:
        schema_extra = {
            "example": {
                "property_key": "screen_size",
                "entity_type": "Laptop",
                "data_type": "FLOAT",
                "unit": "inches",
                "translations": [
                    {"locale": "en", "label": "Screen Size"},
                    {"locale": "es-ES", "label": "Tamaño de Pantalla"}
                ],
                "translation_count": 2
            }
        }


class PropertyListItem(PropertyDefinitionBase):
    """Model for a property in a list view."""
    translation_count: int = Field(default=0, description="Number of available translations")
    status: str = Field(..., description="Translation status: 'complete', 'incomplete', or 'none'")

    class Config:
        schema_extra = {
            "example": {
                "property_key": "price",
                "entity_type": "Laptop",
                "data_type": "FLOAT",
                "unit": "USD",
                "translation_count": 5,
                "status": "incomplete"
            }
        }


class PropertyListResponse(BaseModel):
    """Response model for list of properties."""
    properties: List[PropertyListItem] = Field(default=[], description="List of properties")
    total_count: int = Field(..., description="Total number of properties")
    entity_type: Optional[str] = Field(default=None, description="Filtered entity type")

    class Config:
        schema_extra = {
            "example": {
                "properties": [
                    {
                        "property_key": "price",
                        "entity_type": "Laptop",
                        "data_type": "FLOAT",
                        "unit": "USD",
                        "translation_count": 5,
                        "status": "incomplete"
                    }
                ],
                "total_count": 42,
                "entity_type": "Laptop"
            }
        }


class UndocumentedProperty(BaseModel):
    """Model for an undocumented property found in the data."""
    property_key: str = Field(..., description="Property key")
    sample_values: List[Any] = Field(..., description="Sample values from the data")
    suggested_data_type: str = Field(..., description="Suggested data type based on samples")
    occurrence_count: int = Field(..., description="Number of entities with this property")

    class Config:
        schema_extra = {
            "example": {
                "property_key": "warranty_period",
                "sample_values": ["1 year", "2 years", "3 years"],
                "suggested_data_type": "STRING",
                "occurrence_count": 145
            }
        }


class DiscoveryResponse(BaseModel):
    """Response model for property discovery."""
    entity_type: str = Field(..., description="Entity type scanned")
    undocumented_properties: List[UndocumentedProperty] = Field(..., description="Properties without definitions")
    total_undocumented: int = Field(..., description="Count of undocumented properties")
    total_entities_scanned: int = Field(..., description="Number of entities scanned")

    class Config:
        schema_extra = {
            "example": {
                "entity_type": "Laptop",
                "undocumented_properties": [
                    {
                        "property_key": "warranty_period",
                        "sample_values": ["1 year", "2 years"],
                        "suggested_data_type": "STRING",
                        "occurrence_count": 145
                    }
                ],
                "total_undocumented": 3,
                "total_entities_scanned": 250
            }
        }


class PropertyStatistics(BaseModel):
    """Model for property statistics per entity type."""
    entity_type: str = Field(..., description="Entity type")
    total_properties: int = Field(..., description="Total number of properties defined")
    fully_translated_properties: int = Field(..., description="Properties with all translations")
    partially_translated_properties: int = Field(..., description="Properties with some translations")
    untranslated_properties: int = Field(..., description="Properties with no translations")

    class Config:
        schema_extra = {
            "example": {
                "entity_type": "Laptop",
                "total_properties": 25,
                "fully_translated_properties": 15,
                "partially_translated_properties": 8,
                "untranslated_properties": 2
            }
        }


class StatisticsResponse(BaseModel):
    """Response model for overall statistics."""
    entity_types: List[PropertyStatistics] = Field(..., description="Statistics per entity type")
    total_entity_types: int = Field(..., description="Number of entity types")
    total_properties: int = Field(..., description="Total properties across all types")

    class Config:
        schema_extra = {
            "example": {
                "entity_types": [
                    {
                        "entity_type": "Laptop",
                        "total_properties": 25,
                        "fully_translated_properties": 15,
                        "partially_translated_properties": 8,
                        "untranslated_properties": 2
                    }
                ],
                "total_entity_types": 5,
                "total_properties": 120
            }
        }


class PropertyCoverage(BaseModel):
    """Model for translation coverage of a single property."""
    property_key: str = Field(..., description="Property key")
    entity_type: str = Field(..., description="Entity type")
    available_locales: List[str] = Field(..., description="Locales with translations")
    missing_locales: List[str] = Field(..., description="Locales without translations")
    coverage_percentage: float = Field(..., description="Percentage of supported locales with translations")

    class Config:
        schema_extra = {
            "example": {
                "property_key": "price",
                "entity_type": "Laptop",
                "available_locales": ["en", "es-ES", "fr"],
                "missing_locales": ["de", "ar", "pt-BR", "zh-CN"],
                "coverage_percentage": 42.86
            }
        }


class CoverageResponse(BaseModel):
    """Response model for translation coverage report."""
    entity_type: str = Field(..., description="Entity type")
    properties: List[PropertyCoverage] = Field(..., description="Coverage per property")
    overall_coverage_percentage: float = Field(..., description="Overall coverage percentage")
    total_properties: int = Field(..., description="Total number of properties")

    class Config:
        schema_extra = {
            "example": {
                "entity_type": "Laptop",
                "properties": [
                    {
                        "property_key": "price",
                        "entity_type": "Laptop",
                        "available_locales": ["en", "es-ES"],
                        "missing_locales": ["de", "fr"],
                        "coverage_percentage": 50.0
                    }
                ],
                "overall_coverage_percentage": 65.5,
                "total_properties": 25
            }
        }


class EntityTypeInfo(BaseModel):
    """Model for entity type information."""
    entity_type: str = Field(..., description="Entity type label")
    property_count: int = Field(..., description="Number of properties defined")

    class Config:
        schema_extra = {
            "example": {
                "entity_type": "Laptop",
                "property_count": 25
            }
        }


class EntityTypesResponse(BaseModel):
    """Response model for list of entity types."""
    entity_types: List[EntityTypeInfo] = Field(..., description="List of entity types")
    total_count: int = Field(..., description="Total number of entity types")

    class Config:
        schema_extra = {
            "example": {
                "entity_types": [
                    {"entity_type": "Laptop", "property_count": 25},
                    {"entity_type": "Smartphone", "property_count": 30}
                ],
                "total_count": 2
            }
        }


class ImportRequest(BaseModel):
    """Request model for importing property definitions."""
    format: str = Field(..., description="Import format: 'json' or 'csv'")
    data: str = Field(..., description="Data to import (JSON string or CSV content)")
    merge: bool = Field(default=True, description="Merge with existing (true) or replace (false)")

    @validator('format')
    def validate_format(cls, v):
        if v not in ['json', 'csv']:
            raise ValueError("format must be 'json' or 'csv'")
        return v

    class Config:
        schema_extra = {
            "example": {
                "format": "json",
                "data": "[{\"property_key\": \"price\", \"entity_type\": \"Laptop\"}]",
                "merge": True
            }
        }


class ImportResult(BaseModel):
    """Model for import result."""
    created: int = Field(..., description="Number of properties created")
    updated: int = Field(..., description="Number of properties updated")
    errors: List[str] = Field(default=[], description="List of error messages")

    class Config:
        schema_extra = {
            "example": {
                "created": 10,
                "updated": 5,
                "errors": []
            }
        }


class ExportResponse(BaseModel):
    """Response model for export."""
    format: str = Field(..., description="Export format")
    data: str = Field(..., description="Exported data")
    total_properties: int = Field(..., description="Total properties exported")

    class Config:
        schema_extra = {
            "example": {
                "format": "json",
                "data": "[{...}]",
                "total_properties": 42
            }
        }
