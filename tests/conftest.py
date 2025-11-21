"""
Pytest configuration and fixtures for KG Manager tests.

This module provides common fixtures for testing, including database connections,
test data, and mock objects.
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_neo4j_connection():
    """
    Mock Neo4j connection for testing.

    Returns:
        Mock connection object
    """
    mock_conn = Mock()
    mock_conn.execute_query = Mock(return_value=[])
    return mock_conn


@pytest.fixture
def sample_schema_data():
    """
    Sample schema data for testing.

    Returns:
        Dictionary with sample property definitions
    """
    return [
        {
            'key': 'product_model',
            'display_name': 'Product Model',
            'data_type': 'STRING',
            'unit': None
        },
        {
            'key': 'design_body_weight_g',
            'display_name': 'Body Weight',
            'data_type': 'INTEGER',
            'unit': 'g'
        },
        {
            'key': 'inside_ram_capacity',
            'display_name': 'RAM Capacity',
            'data_type': 'INTEGER',
            'unit': 'GB'
        }
    ]


@pytest.fixture
def sample_schema_data_spanish():
    """
    Sample schema data in Spanish for testing.

    Returns:
        Dictionary with sample property definitions in Spanish
    """
    return [
        {
            'key': 'product_model',
            'display_name': 'Modelo de producto',
            'data_type': 'STRING',
            'unit': None
        },
        {
            'key': 'design_body_weight_g',
            'display_name': 'Peso del cuerpo',
            'data_type': 'INTEGER',
            'unit': 'g'
        },
        {
            'key': 'inside_ram_capacity',
            'display_name': 'Capacidad de RAM',
            'data_type': 'INTEGER',
            'unit': 'GB'
        }
    ]


@pytest.fixture
def sample_entity_data():
    """
    Sample entity data for testing.

    Returns:
        Dictionary with sample entity properties
    """
    return {
        'product_model': 'ASUS Chromebook Flip C433TA-AJ0121',
        'design_body_weight_g': 1500,
        'design_body_thickness_mm': 15.7,
        'inside_ram_capacity': 8,
        'inside_ssd_total_ssd_capacity': 128,
        'display_diagonal': '14.0 in',
        'has_touchscreen': True
    }


@pytest.fixture
def sample_coverage_data():
    """
    Sample translation coverage data for testing.

    Returns:
        List with sample coverage information
    """
    return {
        'entity_type': 'Laptop',
        'expected_locales': ['en', 'es-ES', 'fr', 'de', 'ar', 'pt-BR', 'zh-CN'],
        'total_properties': 3,
        'properties': [
            {
                'property': 'product_model',
                'available_locales': ['es-ES', 'fr', 'de', 'ar', 'pt-BR', 'zh-CN'],
                'missing_locales': [],
                'coverage_count': 6,
                'coverage_percentage': 100.0
            },
            {
                'property': 'design_body_weight_g',
                'available_locales': ['es-ES', 'fr', 'de'],
                'missing_locales': ['ar', 'pt-BR', 'zh-CN'],
                'coverage_count': 3,
                'coverage_percentage': 50.0
            },
            {
                'property': 'inside_ram_capacity',
                'available_locales': ['es-ES'],
                'missing_locales': ['fr', 'de', 'ar', 'pt-BR', 'zh-CN'],
                'coverage_count': 1,
                'coverage_percentage': 16.7
            }
        ]
    }


@pytest.fixture
def mock_translation_cache():
    """
    Mock translation cache for testing.

    Returns:
        Mock cache object
    """
    mock_cache = Mock()
    mock_cache.get = Mock(return_value=None)
    mock_cache.set = Mock()
    mock_cache.invalidate = Mock()
    mock_cache.invalidate_all = Mock()
    mock_cache.invalidate_locale = Mock()
    mock_cache.invalidate_entity_type = Mock()
    return mock_cache
