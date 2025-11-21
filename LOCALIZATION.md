# Multilingual Property Schema - Implementation Guide

## Overview

The KG Manager application now supports multilingual property schemas, allowing property names and metadata to be displayed in multiple languages while maintaining English technical property keys in the database.

## Architecture

### Design Principles

1. **Separation of Concerns**: Technical property keys remain in English in the database; translations exist as metadata
2. **Application-Layer Translation**: All localization happens at the application layer via Neo4j queries
3. **Fallback Strategy**: Missing translations fall back to technical property keys
4. **Caching**: Translation data is cached with TTL to minimize database queries

### Database Schema

The multilingual support uses two node types in Neo4j:

#### PropertyDefinition Node
Metadata about each property.

**Properties:**
- `property_key` (STRING, indexed): Technical property key (e.g., `design_body_weight_g`)
- `entity_type` (STRING): Entity type this property belongs to (e.g., `Laptop`)
- `data_type` (STRING): Data type (e.g., `INTEGER`, `STRING`, `BOOLEAN`)
- `unit` (STRING): Unit of measurement (e.g., `g`, `mm`, `GB`)

**Example:**
```cypher
CREATE (pd:PropertyDefinition {
  property_key: "design_body_weight_g",
  entity_type: "Laptop",
  data_type: "INTEGER",
  unit: "g"
})
```

#### PropertyLabel Node
Translations for property display names.

**Properties:**
- `locale` (STRING): BCP 47 locale code (e.g., `es-ES`, `pt-BR`)
- `label` (STRING): Translated display name

**Example:**
```cypher
CREATE (pl:PropertyLabel {
  locale: "es-ES",
  label: "Peso del cuerpo"
})
```

#### Relationship
```cypher
(PropertyDefinition)-[:HAS_LABEL]->(PropertyLabel)
```

### Application Components

#### 1. Locale Configuration (`backend/utils/locales.py`)

Defines supported locales and provides validation utilities.

**Supported Locales:**
- `en` - English (default)
- `ar` - Arabic (RTL)
- `de` - German
- `es-ES` - Spanish (Spain)
- `fr` - French
- `pt-BR` - Portuguese (Brazil)
- `zh-CN` - Chinese (Simplified)

**Key Functions:**
- `normalize_locale(locale)` - Validates and normalizes locale codes
- `get_all_locales()` - Returns list of supported locales
- `is_locale_supported(locale)` - Checks if locale is supported

#### 2. Localization Utilities (`backend/utils/localization.py`)

Provides caching, fallback logic, and helper functions.

**TranslationCache:**
- In-memory cache with configurable TTL (default: 60 minutes)
- Methods: `get()`, `set()`, `invalidate()`, `invalidate_all()`
- Locale-specific and entity-type-specific invalidation

**Helper Functions:**
- `apply_translation_fallback()` - Handles missing translations
- `humanize_property_key()` - Converts technical keys to readable labels
- `format_property_value()` - Formats values for display

#### 3. Database Queries (`backend/db/localization.py`)

Neo4j queries for multilingual operations.

**LocalizationQueries Class:**
- `get_schema_for_locale(entity_type, locale)` - Get property schema with translations
- `get_entity_with_localized_properties(entity_type, entity_id, locale)` - Get entity with localized properties
- `get_translation_coverage(entity_type)` - Get translation coverage report
- `get_available_locales_for_entity_type(entity_type)` - Get locales with translations

#### 4. Pydantic Models (`backend/models/localization.py`)

Type-safe API request/response models.

**Models:**
- `LocaleInfo` - Locale metadata
- `LocalesResponse` - Response for `/api/locales`
- `SchemaResponse` - Response for `/api/schema/{entity_type}`
- `EntityResponse` - Response for `/api/{entity_type}/{id}`
- `TranslationCoverageResponse` - Response for `/api/translation-coverage/{entity_type}`

## API Endpoints

### 1. GET /api/locales

Get list of supported locales.

**Query Parameters:** None

**Response:**
```json
{
  "locales": [
    {
      "code": "en",
      "name": "English",
      "rtl": false
    },
    {
      "code": "es-ES",
      "name": "Spanish (Spain)",
      "rtl": false
    }
  ],
  "default_locale": "en",
  "total_count": 7
}
```

**Example:**
```bash
curl http://localhost:8000/api/locales
```

---

### 2. GET /api/schema/{entity_type}

Get property schema with localized labels.

**Path Parameters:**
- `entity_type` - Entity type (e.g., `Laptop`, `Smartphone`)

**Query Parameters:**
- `locale` (optional) - Locale code (defaults to `en`)

**Response:**
```json
{
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
```

**Examples:**
```bash
# Get schema in default locale (English)
curl http://localhost:8000/api/schema/Laptop

# Get schema in Spanish
curl http://localhost:8000/api/schema/Laptop?locale=es-ES

# Get schema in French
curl http://localhost:8000/api/schema/Laptop?locale=fr
```

---

### 3. GET /api/{entity_type}/{entity_id}

Get entity with localized property names.

**Path Parameters:**
- `entity_type` - Entity type (e.g., `Laptop`)
- `entity_id` - Entity identifier

**Query Parameters:**
- `locale` (optional) - Locale code (defaults to `en`)

**Response:**
```json
{
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
```

**Examples:**
```bash
# Get entity in default locale (English)
curl http://localhost:8000/api/Laptop/ASUS-Chromebook-Flip-C433TA-AJ0121

# Get entity in Spanish
curl "http://localhost:8000/api/Laptop/ASUS-Chromebook-Flip-C433TA-AJ0121?locale=es-ES"

# Get entity in French
curl "http://localhost:8000/api/Laptop/ASUS-Chromebook-Flip-C433TA-AJ0121?locale=fr"
```

---

### 4. GET /api/translation-coverage/{entity_type}

Get translation coverage report.

**Path Parameters:**
- `entity_type` - Entity type (e.g., `Laptop`)

**Query Parameters:** None

**Response:**
```json
{
  "entity_type": "Laptop",
  "expected_locales": ["en", "es-ES", "fr", "de", "ar", "pt-BR", "zh-CN"],
  "total_properties": 10,
  "properties": [
    {
      "property": "product_model",
      "available_locales": ["es-ES", "fr", "de", "ar", "pt-BR", "zh-CN"],
      "missing_locales": [],
      "coverage_count": 6,
      "coverage_percentage": 100.0
    },
    {
      "property": "design_body_weight_g",
      "available_locales": ["es-ES", "fr", "de"],
      "missing_locales": ["ar", "pt-BR", "zh-CN"],
      "coverage_count": 3,
      "coverage_percentage": 50.0
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/translation-coverage/Laptop
```

## Usage Examples

### Frontend Integration

#### 1. Building a Locale Selector

```javascript
// Fetch available locales
fetch('/api/locales')
  .then(response => response.json())
  .then(data => {
    const localeSelector = document.getElementById('locale-selector');
    data.locales.forEach(locale => {
      const option = document.createElement('option');
      option.value = locale.code;
      option.textContent = locale.name;
      if (locale.code === data.default_locale) {
        option.selected = true;
      }
      localeSelector.appendChild(option);
    });
  });
```

#### 2. Displaying Localized Entity Data

```javascript
const entityType = 'Laptop';
const entityId = 'ASUS-Chromebook-Flip-C433TA-AJ0121';
const locale = 'es-ES';

fetch(`/api/${entityType}/${entityId}?locale=${locale}`)
  .then(response => response.json())
  .then(data => {
    const table = document.getElementById('properties-table');
    data.properties.forEach(prop => {
      const row = table.insertRow();
      row.insertCell(0).textContent = prop.display_name;
      row.insertCell(1).textContent = `${prop.value} ${prop.unit || ''}`;
    });
  });
```

#### 3. Building a Dynamic Form with Localized Labels

```javascript
const locale = document.getElementById('locale-selector').value;

fetch(`/api/schema/Laptop?locale=${locale}`)
  .then(response => response.json())
  .then(schema => {
    const form = document.getElementById('entity-form');
    schema.properties.forEach(prop => {
      const label = document.createElement('label');
      label.textContent = prop.display_name;

      const input = document.createElement('input');
      input.name = prop.key;
      input.type = prop.data_type === 'INTEGER' ? 'number' : 'text';

      form.appendChild(label);
      form.appendChild(input);
    });
  });
```

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Get supported locales
locales_response = requests.get(f"{BASE_URL}/api/locales")
locales = locales_response.json()
print(f"Supported locales: {[loc['code'] for loc in locales['locales']]}")

# Get schema in Spanish
schema_response = requests.get(
    f"{BASE_URL}/api/schema/Laptop",
    params={"locale": "es-ES"}
)
schema = schema_response.json()
print(f"\nSchema for {schema['entity_type']} in {schema['locale']}:")
for prop in schema['properties']:
    print(f"  - {prop['display_name']} ({prop['key']})")

# Get entity with French labels
entity_response = requests.get(
    f"{BASE_URL}/api/Laptop/ASUS-Chromebook-Flip-C433TA-AJ0121",
    params={"locale": "fr"}
)
entity = entity_response.json()
print(f"\nEntity: {entity['id']}")
for prop in entity['properties']:
    print(f"  {prop['display_name']}: {prop['value']} {prop['unit'] or ''}")

# Check translation coverage
coverage_response = requests.get(f"{BASE_URL}/api/translation-coverage/Laptop")
coverage = coverage_response.json()
print(f"\nTranslation coverage for {coverage['entity_type']}:")
for prop in coverage['properties']:
    print(f"  {prop['property']}: {prop['coverage_percentage']}%")
```

## Error Handling

### Fallback Behavior

1. **Unsupported Locale**: Falls back to default locale (`en`)
   ```bash
   # Request with invalid locale returns English
   curl "http://localhost:8000/api/schema/Laptop?locale=xx-YY"
   # Response will have "locale": "en"
   ```

2. **Missing Translation**: Uses technical property key
   ```json
   {
     "key": "new_untranslated_property",
     "display_name": "new_untranslated_property",
     "data_type": "STRING",
     "unit": null
   }
   ```

3. **Entity Not Found**: Returns 404
   ```bash
   curl http://localhost:8000/api/Laptop/nonexistent-id
   # Response: 404 with error detail
   ```

### Error Responses

```json
{
  "detail": "Entity not found: Laptop with id 'nonexistent-id'"
}
```

## Caching Strategy

### Cache Configuration

- **TTL**: 60 minutes (configurable in `TranslationCache`)
- **Cache Keys**:
  - Schema: `schema:{entity_type}:{locale}`
  - Coverage: `coverage:{entity_type}`

### Cache Invalidation

```python
from backend.db.localization import get_localization_queries

localization = get_localization_queries(connection)

# Invalidate cache for specific entity type
localization.invalidate_cache_for_entity_type('Laptop')

# Invalidate cache for specific locale
localization.invalidate_cache_for_locale('es-ES')

# Invalidate all caches
localization.invalidate_all_caches()
```

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_locales.py

# Run with coverage
pytest --cov=backend tests/
```

### Test Files

- `tests/test_locales.py` - Locale configuration tests
- `tests/test_localization_utils.py` - Utility function tests
- `tests/test_api_localization.py` - API endpoint tests

## Extending to New Locales

### Adding a New Locale

1. **Update locale configuration** (`backend/utils/locales.py`):
   ```python
   SUPPORTED_LOCALES: Dict[str, LocaleInfo] = {
       # ... existing locales ...
       'ja': LocaleInfo(code='ja', name='Japanese', rtl=False),
   }
   ```

2. **Add translations to Neo4j**:
   ```cypher
   // Add PropertyDefinitions if not exists
   MERGE (pd:PropertyDefinition {property_key: "design_body_weight_g", entity_type: "Laptop"})
   ON CREATE SET pd.data_type = "INTEGER", pd.unit = "g"

   // Add Japanese translation
   CREATE (pl:PropertyLabel {locale: "ja", label: "本体重量"})
   CREATE (pd)-[:HAS_LABEL]->(pl)
   ```

3. **Invalidate caches**:
   ```python
   localization.invalidate_all_caches()
   ```

## Performance Considerations

### Optimization Tips

1. **Use Caching**: Enable caching for production (default: enabled)
2. **Batch Requests**: Fetch schema once, reuse for multiple entities
3. **Limit Locales**: Only add locales you actively support
4. **Index Properties**: Ensure `property_key` is indexed in Neo4j
   ```cypher
   CREATE INDEX property_key_index FOR (pd:PropertyDefinition) ON (pd.property_key)
   ```

### Monitoring

Check cache statistics:
```python
from backend.utils.localization import get_translation_cache

cache = get_translation_cache()
stats = cache.get_stats()
print(f"Cache entries: {stats['entry_count']}")
```

## Troubleshooting

### Common Issues

**Issue**: Translations not appearing
- **Solution**: Check that PropertyDefinition and PropertyLabel nodes exist with correct relationships
- **Verify**:
  ```cypher
  MATCH (pd:PropertyDefinition {property_key: "design_body_weight_g"})
        -[:HAS_LABEL]->(pl:PropertyLabel {locale: "es-ES"})
  RETURN pd, pl
  ```

**Issue**: Cache not invalidating
- **Solution**: Use appropriate invalidation method for your use case
- **Example**: `localization.invalidate_cache_for_entity_type('Laptop')`

**Issue**: 404 errors for valid entities
- **Solution**: Check that entity ID property matches expected property name
- **Note**: Default tries `product_model`, `_id`, `id`, `name`, `model`, `code`

## Best Practices

1. **Always provide fallback**: Use technical keys when translations missing
2. **Log missing translations**: Track gaps for future translation work
3. **Use BCP 47 codes**: Standard locale codes (e.g., `es-ES`, not `es_ES`)
4. **Cache aggressively**: Translation data rarely changes
5. **Invalidate selectively**: Only invalidate what changed
6. **Test all locales**: Ensure coverage is complete before release
7. **Document translations**: Keep track of who translated what and when

## Migration Guide for Existing Clients

### Updating API Calls

**Before:**
```javascript
fetch(`/api/entities/Laptop/${entityId}`)
```

**After:**
```javascript
const locale = getCurrentLocale(); // Get from user preference
fetch(`/api/Laptop/${entityId}?locale=${locale}`)
```

### Response Format Changes

**Before:**
```json
{
  "design_body_weight_g": 1500
}
```

**After:**
```json
{
  "properties": [
    {
      "technical_key": "design_body_weight_g",
      "display_name": "Peso del cuerpo",
      "value": "1500",
      "unit": "g"
    }
  ]
}
```

## Future Enhancements

- [ ] Admin UI for managing translations
- [ ] Translation import/export (CSV, JSON)
- [ ] Machine translation integration
- [ ] Translation versioning and history
- [ ] User-contributed translations
- [ ] Locale-specific formatting (numbers, dates)
- [ ] Plural forms support
- [ ] Gender-specific translations (where applicable)

## Support

For issues or questions:
- GitHub Issues: [Your repository issues URL]
- Documentation: This file
- Neo4j Cypher Reference: https://neo4j.com/docs/cypher-manual/current/

---

**Last Updated**: 2024-11-21
**Version**: 1.0.0
