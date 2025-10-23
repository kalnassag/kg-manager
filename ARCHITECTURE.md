# Architecture Documentation

## Overview

The Product Knowledge Graph Manager is built with a modular, entity-type agnostic architecture that automatically adapts to any Neo4j graph schema.

## Design Principles

### 1. Entity-Type Agnostic
- **No hardcoded entity types**: All node labels are discovered at runtime
- **Dynamic property grouping**: Properties grouped by naming patterns
- **Flexible validation**: Rules based on property name conventions
- **Automatic categorization**: Products vs. supporting entities determined heuristically

### 2. Convention Over Configuration
- **Property naming**: Prefixes determine grouping and validation
  - `product_*` → Product information
  - `design_*` → Design specifications
  - `inside_*` → Internal specifications
  - `has_*` → Boolean features
- **Display names**: Priority order for identifying properties
- **Relationship exploration**: Bi-directional navigation

### 3. Performance First
- **Lazy loading**: Relationships loaded only when needed
- **Pagination**: Large datasets handled efficiently
- **Connection pooling**: Neo4j driver manages connections
- **Minimal queries**: Optimized Cypher patterns

## Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend Layer                       │
│  (HTML Templates + HTMX + CSS + JavaScript)             │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP Requests
┌─────────────────▼───────────────────────────────────────┐
│                   FastAPI Application                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Routes (app.py)                                   │   │
│  │  - Home, List, Detail, Edit, Create, Delete      │   │
│  │  - Search, API endpoints                          │   │
│  └──────────────┬───────────────────────────────────┘   │
│                 │                                         │
│  ┌──────────────▼───────────────────────────────────┐   │
│  │ Utilities                                         │   │
│  │  - Display name computation                       │   │
│  │  - Property grouping                              │   │
│  │  - Value validation                               │   │
│  └──────────────┬───────────────────────────────────┘   │
│                 │                                         │
│  ┌──────────────▼───────────────────────────────────┐   │
│  │ Database Layer                                    │   │
│  │  - Connection management                          │   │
│  │  - Schema discovery                               │   │
│  │  - CRUD queries                                   │   │
│  └──────────────┬───────────────────────────────────┘   │
└─────────────────┼───────────────────────────────────────┘
                  │ Cypher Queries
┌─────────────────▼───────────────────────────────────────┐
│                     Neo4j Database                       │
│  (Graph structure with nodes and relationships)          │
└─────────────────────────────────────────────────────────┘
```

## Key Modules

### Backend

#### `app.py` - FastAPI Application
- **Purpose**: HTTP request handling and routing
- **Responsibilities**:
  - Define all routes (home, list, detail, edit, create, delete, search)
  - Handle form submissions
  - Render templates with appropriate context
  - Error handling
- **Dependencies**: Templates, utilities, database layer

#### `config.py` - Configuration Management
- **Purpose**: Centralized configuration
- **Responsibilities**:
  - Load YAML configuration
  - Provide typed access to settings
  - Validate configuration values
- **Pattern**: Singleton pattern for global config instance

### Database Layer

#### `connection.py` - Neo4j Connection
- **Purpose**: Manage database connections
- **Responsibilities**:
  - Initialize Neo4j driver
  - Execute queries and write operations
  - Connection lifecycle management
- **Pattern**: Singleton pattern for global connection

#### `discovery.py` - Schema Discovery
- **Purpose**: Automatically discover graph structure
- **Responsibilities**:
  - Discover node labels
  - Analyze properties per label
  - Categorize entity types
  - Discover relationships
  - Cache schema information
- **Key Methods**:
  - `discover_node_labels()`: Get all labels
  - `get_node_properties(label)`: Get properties for a label
  - `categorize_labels()`: Split into products vs. supporting
  - `get_entity_relationships()`: Get all relationships for an entity

#### `queries.py` - CRUD Operations
- **Purpose**: Execute database operations
- **Responsibilities**:
  - List entities with pagination
  - Get single entities
  - Create, update, delete entities
  - Manage relationships
  - Search across entities
- **Key Methods**:
  - `get_entities()`: Paginated list
  - `get_entity_by_id()`: Single entity
  - `create_entity()`, `update_entity()`, `delete_entity()`
  - `search_entities()`: Global search

### Utilities

#### `display.py` - Display Name Logic
- **Purpose**: Compute human-readable names for entities
- **Responsibilities**:
  - Determine display name from properties
  - Include brand in display name
  - Humanize labels and property names
  - Format IDs
- **Algorithm**:
  ```python
  Priority:
  1. product_model
  2. model
  3. name
  4. version
  5. First string property
  6. Formatted _id
  ```

#### `grouping.py` - Property Organization
- **Purpose**: Group properties by logical sections
- **Responsibilities**:
  - Parse property prefixes
  - Map to human-readable groups
  - Handle nested sub-groups
  - Sort groups by priority
- **Structure**:
  ```python
  {
    'Main Group': {
      'Sub Group': {
        'property_name': value
      }
    }
  }
  ```

#### `validation.py` - Value Validation
- **Purpose**: Validate property values
- **Responsibilities**:
  - Determine expected type from property name
  - Validate values against expected type
  - Convert string inputs to appropriate types
  - Generate HTML input types
- **Rules**:
  - `has_*` → boolean
  - `*_mm`, `*_g`, `*_wh` → numeric
  - `number_of_*` → integer
  - Default → string

### Frontend

#### Templates
- **`base.html`**: Layout with navbar, footer, common structure
- **`home.html`**: Dashboard with stats and entity type cards
- **`entity_list.html`**: Paginated list/table view
- **`entity_detail.html`**: Property groups + relationships
- **`entity_edit.html`**: Edit form with validation
- **`entity_create.html`**: Create form
- **`search.html`**: Global search results

#### CSS (`style.css`)
- **Theme**: Light blue and white professional design
- **Variables**: CSS custom properties for easy theming
- **Layout**: Flexbox and Grid for responsive design
- **Components**: Reusable button, card, form styles
- **Responsive**: Mobile-friendly breakpoints

#### JavaScript (`app.js`)
- **Purpose**: Client-side enhancements
- **Features**:
  - View mode preference storage
  - Form validation
  - Delete confirmations
  - Notifications
- **Pattern**: Progressive enhancement (works without JS)

## Data Flow

### Viewing an Entity

```
User clicks entity
    ↓
GET /entities/{label}/{id}
    ↓
app.py: view_entity()
    ↓
queries.get_entity_by_id()  ← Neo4j query
    ↓
discovery.get_entity_relationships()  ← Neo4j query
    ↓
grouping.group_properties()
    ↓
display.get_display_name_with_brand()
    ↓
Render entity_detail.html
    ↓
Return HTML to browser
```

### Creating an Entity

```
User submits form
    ↓
POST /entities/{label}/new
    ↓
app.py: create_entity()
    ↓
Validate form data (validation.py)
    ↓
Convert values (validation.py)
    ↓
queries.create_entity()  ← Neo4j CREATE
    ↓
Redirect to entity list
```

### Discovery Process

```
Application startup
    ↓
initialize_connection()
    ↓
get_discovery().get_all_schema_info()
    ↓
discover_node_labels()  ← CALL db.labels()
    ↓
For each label:
  get_node_properties()  ← MATCH (n:Label) RETURN keys(n)
  get_node_count()       ← MATCH (n:Label) RETURN count(n)
    ↓
categorize_labels()
    ↓
discover_relationships()  ← CALL db.relationshipTypes()
    ↓
Return schema information
    ↓
Cache in memory
```

## Extension Points

### Adding New Property Groups

Edit `backend/utils/grouping.py`:

```python
group_mappings = {
    'new_prefix': ('Display Name', {
        'sub1': 'Sub Group 1',
        'sub2': 'Sub Group 2'
    })
}
```

### Adding Custom Validation

Edit `backend/utils/validation.py`:

```python
def get_property_type(prop_name: str) -> str:
    if prop_name.startswith('custom_'):
        return 'custom_type'
    # existing logic...
```

### Adding New Routes

Edit `backend/app.py`:

```python
@app.get("/custom/route")
async def custom_route(request: Request):
    # Your logic
    return templates.TemplateResponse("custom.html", {...})
```

### Custom Relationship Handling

Edit `backend/db/discovery.py`:

```python
def get_special_relationships(self, label: str, node_id: str):
    # Custom relationship logic
    pass
```

## Security Considerations

### Current Implementation
- **No authentication**: Open access to all features
- **No authorization**: No role-based access control
- **Cypher injection**: Parameterized queries prevent injection
- **XSS protection**: Jinja2 auto-escapes HTML

### Production Recommendations
1. Add authentication (OAuth, JWT, etc.)
2. Implement role-based access control
3. Add HTTPS/TLS
4. Rate limiting for API endpoints
5. Audit logging for all changes
6. Input sanitization beyond basic validation

## Performance Optimization

### Current Optimizations
- Pagination (configurable page size)
- Connection pooling (Neo4j driver)
- Lazy relationship loading
- Indexed queries on `_id`
- Efficient Cypher patterns

### Recommended Improvements
1. **Caching**: Redis for schema info, entity counts
2. **Indexes**: Create indexes on frequently queried properties
3. **Query optimization**: Use EXPLAIN/PROFILE for slow queries
4. **Async operations**: More async/await patterns
5. **CDN**: Static assets via CDN in production

## Testing Strategy

### Unit Tests
```python
# test_display.py
def test_get_display_name():
    node = {'product_model': 'EliteBook 630'}
    assert get_display_name(node) == 'EliteBook 630'

# test_validation.py
def test_validate_numeric_property():
    is_valid, _ = validate_value('inside_ram_size_gb', 16)
    assert is_valid
```

### Integration Tests
```python
# test_queries.py
@pytest.mark.asyncio
async def test_create_entity():
    entity = queries.create_entity('Laptop', {'_id': 'test-1'})
    assert entity['_id'] == 'test-1'
```

### End-to-End Tests
- Use Playwright or Selenium
- Test full user workflows
- Verify UI interactions

## Deployment

### Development
```bash
uvicorn backend.app:app --reload
```

### Production
```bash
# Using Gunicorn with Uvicorn workers
gunicorn backend.app:app -w 4 -k uvicorn.workers.UvicornWorker

# Or with Docker
docker build -t kg-manager .
docker run -p 8000:8000 kg-manager
```

### Environment Variables
```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=secret
```

## Monitoring

### Recommended Metrics
- Request latency
- Neo4j query performance
- Error rates
- Active connections
- Memory usage

### Logging
- Application logs: FastAPI built-in logging
- Neo4j query logs: Enable in driver
- Access logs: Uvicorn/Gunicorn

## Future Enhancements

### Planned Features
1. **Bulk import/export**: CSV/JSON import/export
2. **Advanced search**: Full-text search, filters
3. **Graph visualization**: Interactive graph views
4. **Relationship management**: UI for creating/deleting relationships
5. **History tracking**: Audit log of changes
6. **API documentation**: Auto-generated OpenAPI docs
7. **WebSocket support**: Real-time updates
8. **Multi-tenancy**: Support multiple knowledge graphs

### Technical Improvements
1. **TypeScript**: Type-safe frontend
2. **React/Vue**: Modern SPA framework
3. **GraphQL**: Alternative to REST
4. **Elasticsearch**: Better search capabilities
5. **Background tasks**: Celery for async operations
