# Product Knowledge Graph Manager

A professional web application for managing and exploring Neo4j knowledge graphs containing product technical specifications. Built with FastAPI and HTMX for fast, responsive interaction.

## Features

### 🎯 Core Capabilities

- **Entity-Type Agnostic Design**: Automatically discovers and adapts to any node types in your Neo4j database
- **Dynamic Property Grouping**: Intelligently organizes properties by prefix patterns (e.g., `design_*`, `inside_cpu_*`)
- **Full CRUD Operations**: Create, read, update, and delete entities with validation
- **Relationship Navigation**: Explore connections between entities intuitively
- **Dual View Modes**: Toggle between list and table views
- **Global Search**: Search across all entity types
- **Professional UI**: Clean light blue and white theme with compact, readable layout

### 🔍 Auto-Discovery System

The application automatically:
- Discovers all node labels (entity types) in your database
- Categorizes them into "Product Types" and "Supporting Entities"
- Analyzes property patterns and groups them intelligently
- Detects relationship types and displays them contextually
- Requires **zero code changes** when adding new product types

### 📊 Property Organization

Properties are automatically grouped by prefix:
- `product_*` → Product Information
- `design_*` → Design & Build (with sub-groups: body, keyboard, touchpad)
- `inside_*` → Technical Specifications (with sub-groups: cpu, ram, gpu, ssd, etc.)
- `display_*` → Display
- `camera_*` → Camera
- `has_*` → Features

## Architecture

### Technology Stack

- **Backend**: FastAPI (Python 3.8+)
- **Database**: Neo4j
- **Frontend**: HTML, HTMX, CSS, JavaScript
- **Templating**: Jinja2

### Project Structure

```
product_graph_manager/
├── backend/
│   ├── app.py                  # Main FastAPI application
│   ├── config.py               # Configuration management
│   ├── db/
│   │   ├── connection.py       # Neo4j connection manager
│   │   ├── discovery.py        # Schema discovery system
│   │   └── queries.py          # CRUD query functions
│   └── utils/
│       ├── display.py          # Display name computation
│       ├── grouping.py         # Property grouping logic
│       └── validation.py       # Value validation
├── static/
│   ├── css/
│   │   └── style.css          # Professional styling
│   └── js/
│       └── app.js             # Client-side functionality
├── templates/                  # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── entity_list.html
│   ├── entity_detail.html
│   ├── entity_edit.html
│   ├── entity_create.html
│   └── search.html
├── config.yaml                 # Application configuration
├── requirements.txt            # Python dependencies
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Neo4j database (running locally or remotely)
- Neo4j database with existing product data

### Installation

1. **Clone or download the project**

   ```bash
   cd kg-manager
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the application**

   Copy the configuration template:
   ```bash
   cp config.yaml.template config.yaml
   ```

   Edit `config.yaml` with your Neo4j credentials:
   ```yaml
   neo4j:
     uri: "bolt://localhost:7687"
     user: "neo4j"
     password: "your_password_here"

   app:
     host: "0.0.0.0"
     port: 8000
     debug: true

   ui:
     items_per_page: 100
     default_view: "list"
   ```

5. **Run the application**

   ```bash
   python -m backend.app
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the application**

   Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## How It Works

### Discovery System

On startup, the application:

1. **Connects to Neo4j** and verifies connectivity
2. **Discovers all node labels** using `CALL db.labels()`
3. **Analyzes each label** to determine:
   - Property names and types
   - Average property count
   - Presence of product-like properties
4. **Categorizes labels**:
   - **Product Types**: Labels with >10 properties or product-specific prefixes
   - **Supporting Entities**: Other labels (brands, models, colors, etc.)
5. **Discovers relationships** and their source/target patterns

### Display Name Logic

When showing entities, the system computes display names by:

1. Checking properties in priority order:
   - `product_model`
   - `model`
   - `name`
   - `version`
   - `title`
2. If none exist, uses the first non-internal string property
3. If brand relationship exists, prepends it (e.g., "HP EliteBook 630 G9")
4. Falls back to formatted `_id`

### Property Grouping

Properties are grouped by prefix pattern:

```python
# Example: design_body_material
parts = ['design', 'body', 'material']
main_group = 'Design & Build'
sub_group = 'Body'
display_name = 'Material'
```

### Validation

Values are validated based on property naming:

- **Boolean**: Properties starting with `has_` or `is_`
- **Numeric**: Properties ending with `_mm`, `_g`, `_wh`, etc., or containing keywords like "speed", "capacity"
- **Integer**: Properties containing "number_of" or ending with "_count"
- **String**: Everything else

## Usage Guide

### Home Dashboard

- View statistics about your knowledge graph
- See all product types and supporting entities
- Click any entity type to browse

### List View

- **List Mode**: Compact cards showing entities with key properties
- **Table Mode**: Spreadsheet-like view with all properties
- **Search**: Filter entities by any property value
- **Pagination**: Navigate large datasets efficiently

### Detail View

- **Properties Section**: Organized by logical groups
- **Relationships Panel**: Shows all connected entities
- **Actions**: Edit or delete the entity

### Editing Entities

- Click "Edit" on any entity detail page
- Modify properties with appropriate input types
- Changes are validated based on property patterns
- `_id` cannot be changed

### Creating Entities

1. Navigate to an entity list page
2. Click "Create New"
3. Fill in the `_id` (required) and any other properties
4. Submit to create

### Deleting Entities

- Delete button available on detail pages
- Uses `DETACH DELETE` to remove all relationships
- Confirmation required

## Adding New Product Types

The beauty of this system is that **no code changes are required** to support new product types!

### Example: Adding Smartphones

1. **Add smartphone data to Neo4j**:
   ```cypher
   CREATE (p:Smartphone {
     _id: 'iphone-15-pro',
     product_model: 'iPhone 15 Pro',
     design_body_material: 'Titanium',
     inside_cpu_model: 'A17 Pro',
     display_size_inch: 6.1,
     camera_main_mp: 48,
     has_5g: true
   })
   ```

2. **Restart the application** (or wait for auto-reload)

3. **Done!** The dashboard will now show:
   - "Smartphone" in the Product Types section
   - All properties automatically grouped
   - Full CRUD support

The system will:
- Detect the `Smartphone` label
- Categorize it as a product type (due to property patterns)
- Group properties: `design_*`, `inside_*`, `display_*`, `camera_*`, `has_*`
- Generate appropriate forms for create/edit
- Support all relationships

## Performance Considerations

### Optimizations

- **Connection Pooling**: Neo4j driver manages connections efficiently
- **Pagination**: Large result sets are paginated (configurable)
- **Lazy Loading**: Relationships loaded only when viewing details
- **Indexed Queries**: Uses `_id` property for fast lookups

### Recommended Neo4j Indexes

```cypher
CREATE INDEX entity_id IF NOT EXISTS FOR (n:Laptop) ON (n._id);
CREATE INDEX entity_id IF NOT EXISTS FOR (n:Phone) ON (n._id);
-- Add similar indexes for other entity types
```

## Customization

### Changing the Theme

Edit `/static/css/style.css` and modify the CSS variables:

```css
:root {
    --primary-blue: #4A90E2;      /* Main accent color */
    --secondary-blue: #E8F4FD;    /* Light backgrounds */
    --background: #F8FBFE;        /* Page background */
    /* ... */
}
```

### Adjusting Property Groups

Edit `/backend/utils/grouping.py` to customize group mappings:

```python
group_mappings = {
    'product': ('Product Information', None),
    'design': ('Design & Build', {
        'body': 'Body',
        'keyboard': 'Keyboard',
        # Add more sub-groups
    }),
    # Add more main groups
}
```

### Modifying Validation Rules

Edit `/backend/utils/validation.py` to adjust property type detection:

```python
def get_property_type(prop_name: str) -> str:
    # Add custom rules here
    if prop_name.startswith('custom_'):
        return 'custom_type'
    # ...
```

## API Endpoints

The application provides both HTML and JSON endpoints:

- `GET /` - Home dashboard
- `GET /entities/{label}` - List entities
- `GET /entities/{label}/{entity_id}` - View entity
- `GET /entities/{label}/{entity_id}/edit` - Edit form
- `POST /entities/{label}/{entity_id}/edit` - Update entity
- `GET /entities/{label}/new` - Create form
- `POST /entities/{label}/new` - Create entity
- `POST /entities/{label}/{entity_id}/delete` - Delete entity
- `GET /search?q={query}` - Global search
- `GET /api/schema` - Get schema information (JSON)

## Troubleshooting

### Connection Issues

**Problem**: "Failed to connect to Neo4j"

**Solution**:
- Verify Neo4j is running: `systemctl status neo4j` (Linux) or check Neo4j Desktop
- Check URI in `config.yaml` matches your Neo4j instance
- Verify credentials are correct
- Test connection: `curl http://localhost:7474` (default Neo4j HTTP port)

### Empty Dashboard

**Problem**: Dashboard shows zero entities

**Solution**:
- Verify data exists in Neo4j: Run `MATCH (n) RETURN count(n)` in Neo4j Browser
- Check that nodes have the `_id` property
- Review application logs for errors

### Property Grouping Issues

**Problem**: Properties not grouped as expected

**Solution**:
- Properties must follow naming convention: `prefix_subprefix_name`
- Check `/backend/utils/grouping.py` for group mappings
- Add custom groups if needed

## Development

### Running in Development Mode

```bash
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag enables auto-reload on code changes.

### Adding New Features

1. **Backend**: Add routes in `/backend/app.py`
2. **Database**: Add queries in `/backend/db/queries.py`
3. **Frontend**: Add templates in `/templates/`
4. **Styling**: Update `/static/css/style.css`
5. **Logic**: Add utilities in `/backend/utils/`

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests (if test suite is added)
pytest
```

## Contributing

Feel free to submit issues or pull requests for:
- Bug fixes
- New features
- Documentation improvements
- Performance optimizations

## License

This project is provided as-is for educational and commercial use.

## Support

For questions or issues:
1. Check this README
2. Review the code comments
3. Check Neo4j connection and data
4. Review application logs

---

**Built with FastAPI, Neo4j, and HTMX**

*Fast, flexible, and future-proof knowledge graph management.*
