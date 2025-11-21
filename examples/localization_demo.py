#!/usr/bin/env python3
"""
Multilingual Property Schema - Demo Script

This script demonstrates how to use the multilingual property schema API endpoints
to retrieve localized property names and entity data.

Usage:
    python examples/localization_demo.py

Requirements:
    - KG Manager application running at http://localhost:8000
    - Neo4j database with PropertyDefinition and PropertyLabel nodes
    - requests library: pip install requests
"""

import requests
import json
from typing import Dict, List, Any


class LocalizationDemo:
    """Demo client for multilingual property schema API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize demo client.

        Args:
            base_url: Base URL of the KG Manager API
        """
        self.base_url = base_url

    def get_supported_locales(self) -> Dict[str, Any]:
        """
        Get list of supported locales.

        Returns:
            Dictionary with locales list and metadata
        """
        response = requests.get(f"{self.base_url}/api/locales")
        response.raise_for_status()
        return response.json()

    def get_schema(self, entity_type: str, locale: str = None) -> Dict[str, Any]:
        """
        Get property schema for an entity type with localized labels.

        Args:
            entity_type: Entity type (e.g., 'Laptop', 'Smartphone')
            locale: Locale code (e.g., 'es-ES', 'fr')

        Returns:
            Schema with localized property names
        """
        params = {'locale': locale} if locale else {}
        response = requests.get(
            f"{self.base_url}/api/schema/{entity_type}",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_entity(
        self,
        entity_type: str,
        entity_id: str,
        locale: str = None
    ) -> Dict[str, Any]:
        """
        Get an entity with localized property names.

        Args:
            entity_type: Entity type (e.g., 'Laptop')
            entity_id: Entity identifier
            locale: Locale code (e.g., 'es-ES', 'fr')

        Returns:
            Entity data with localized property names
        """
        params = {'locale': locale} if locale else {}
        response = requests.get(
            f"{self.base_url}/api/{entity_type}/{entity_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_translation_coverage(self, entity_type: str) -> Dict[str, Any]:
        """
        Get translation coverage report for an entity type.

        Args:
            entity_type: Entity type (e.g., 'Laptop')

        Returns:
            Translation coverage report
        """
        response = requests.get(
            f"{self.base_url}/api/translation-coverage/{entity_type}"
        )
        response.raise_for_status()
        return response.json()

    def print_json(self, data: Dict[str, Any], title: str = None) -> None:
        """
        Pretty print JSON data.

        Args:
            data: Dictionary to print
            title: Optional title to display
        """
        if title:
            print(f"\n{'='*60}")
            print(f"{title}")
            print('='*60)
        print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    """Run the demo."""
    print("Multilingual Property Schema - Demo")
    print("="*60)

    # Initialize demo client
    demo = LocalizationDemo()

    try:
        # 1. Get supported locales
        print("\n1. Getting supported locales...")
        locales = demo.get_supported_locales()
        demo.print_json(locales, "Supported Locales")

        print(f"\nFound {locales['total_count']} supported locales:")
        for locale in locales['locales']:
            rtl_marker = " (RTL)" if locale['rtl'] else ""
            print(f"  - {locale['code']}: {locale['name']}{rtl_marker}")

        # 2. Get schema in default locale (English)
        print("\n\n2. Getting schema in default locale (English)...")
        schema_en = demo.get_schema('Laptop')
        demo.print_json(schema_en, "Schema for Laptop (English)")

        # 3. Get schema in Spanish
        print("\n\n3. Getting schema in Spanish...")
        schema_es = demo.get_schema('Laptop', locale='es-ES')
        demo.print_json(schema_es, "Schema for Laptop (Spanish)")

        # 4. Compare property names
        print("\n\n4. Comparing property names across locales:")
        print(f"\n{'Property Key':<30} {'English':<30} {'Spanish':<30}")
        print("-"*90)

        # Create dictionaries for easy lookup
        en_props = {p['key']: p['display_name'] for p in schema_en['properties']}
        es_props = {p['key']: p['display_name'] for p in schema_es['properties']}

        for key in sorted(en_props.keys()):
            en_name = en_props.get(key, key)
            es_name = es_props.get(key, key)
            print(f"{key:<30} {en_name:<30} {es_name:<30}")

        # 5. Get translation coverage
        print("\n\n5. Getting translation coverage report...")
        coverage = demo.get_translation_coverage('Laptop')
        demo.print_json(coverage, "Translation Coverage for Laptop")

        # Show summary
        print("\n\nTranslation Coverage Summary:")
        print(f"Total properties: {coverage['total_properties']}")
        print(f"Expected locales: {', '.join(coverage['expected_locales'])}")
        print("\nProperties by coverage:")

        # Sort by coverage percentage
        sorted_props = sorted(
            coverage['properties'],
            key=lambda p: p['coverage_percentage'],
            reverse=True
        )

        for prop in sorted_props:
            coverage_bar = '█' * int(prop['coverage_percentage'] / 10)
            print(
                f"  {prop['property']:<35} "
                f"{prop['coverage_percentage']:>5.1f}% "
                f"{coverage_bar}"
            )

        # 6. Try getting an entity (if one exists)
        print("\n\n6. Getting entity with localized properties...")
        print("Note: This requires a valid entity ID from your database.")
        print("Example usage:")
        print("  entity = demo.get_entity('Laptop', 'ASUS-Chromebook-Flip', locale='fr')")

        # Example response structure
        example_entity = {
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
        demo.print_json(example_entity, "Example Entity Response")

        print("\n\n" + "="*60)
        print("Demo completed successfully!")
        print("="*60)

    except requests.exceptions.ConnectionError:
        print("\n\nError: Could not connect to KG Manager API.")
        print("Please ensure the application is running at http://localhost:8000")
    except requests.exceptions.HTTPError as e:
        print(f"\n\nHTTP Error: {e}")
        print("This might be because:")
        print("  - Entity type doesn't exist in the database")
        print("  - PropertyDefinition nodes are not created yet")
        print("  - Database connection is not configured")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")


if __name__ == "__main__":
    main()
