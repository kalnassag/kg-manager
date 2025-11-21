"""Main FastAPI application for Product Knowledge Graph Manager."""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import logging
from pathlib import Path

from .config import config
from .db.connection import initialize_connection, close_connection
from .db.discovery import get_discovery
from .db.queries import get_queries
from .utils.display import (
    get_display_name,
    get_display_name_with_brand,
    get_entity_id,
    humanize_label,
    humanize_property_name,
    humanize_relationship_type
)
from .utils.grouping import group_properties, sort_groups
from .utils.validation import validate_value, convert_value, get_input_type

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Product Knowledge Graph Manager")

# Setup static files and templates
BASE_DIR = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Add utility functions to Jinja2 environment
templates.env.globals.update({
    'get_display_name': get_display_name,
    'get_entity_id': get_entity_id,
    'humanize_label': humanize_label,
    'humanize_property_name': humanize_property_name,
    'humanize_relationship_type': humanize_relationship_type,
    'get_input_type': get_input_type
})

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    try:
        initialize_connection(
            config.neo4j_uri,
            config.neo4j_user,
            config.neo4j_password
        )
        logger.info("Application started successfully")

        # Discover schema
        discovery = get_discovery()
        schema = discovery.get_all_schema_info()
        logger.info(f"Discovered schema: {len(schema['labels'])} labels, "
                   f"{len(schema['product_types'])} product types, "
                   f"{len(schema['supporting_entities'])} supporting entities")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    close_connection()
    logger.info("Application shutdown")

# Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home dashboard."""
    discovery = get_discovery()
    schema = discovery.get_all_schema_info()

    return templates.TemplateResponse("home.html", {
        "request": request,
        "schema": schema
    })

@app.get("/entities/{label}", response_class=HTMLResponse)
async def list_entities(
    request: Request,
    label: str,
    page: int = 1,
    search: Optional[str] = None,
    view: Optional[str] = None
):
    """List view for entities of a specific type."""
    queries = get_queries()
    discovery = get_discovery()

    # Get entities
    result = queries.get_entities(label, page=page, page_size=config.items_per_page, search=search)

    # Get sample for properties
    sample_props = discovery.get_node_properties(label)

    # Determine view mode
    view_mode = view or config.default_view

    return templates.TemplateResponse("entity_list.html", {
        "request": request,
        "label": label,
        "label_human": humanize_label(label),
        "entities": result['items'],
        "total": result['total'],
        "page": result['page'],
        "total_pages": result['total_pages'],
        "page_size": result['page_size'],
        "search": search or "",
        "view_mode": view_mode,
        "sample_props": sorted(sample_props.keys())
    })

@app.get("/entities/{label}/new", response_class=HTMLResponse)
async def create_entity_form(request: Request, label: str):
    """Create form for new entity."""
    discovery = get_discovery()

    # Get sample properties from existing entities
    sample_props = discovery.get_node_properties(label)

    return templates.TemplateResponse("entity_create.html", {
        "request": request,
        "label": label,
        "label_human": humanize_label(label),
        "sample_props": sorted(sample_props.keys())
    })

@app.post("/entities/{label}/new")
async def create_entity(request: Request, label: str):
    """Create a new entity."""
    queries = get_queries()

    # Get form data
    form_data = await request.form()
    properties = {}

    for key, value in form_data.items():
        if not value or value == '':
            continue

        # Convert value
        converted_value = convert_value(key, value)

        # Validate
        is_valid, error = validate_value(key, converted_value)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        properties[key] = converted_value

    # Ensure _id is present
    if '_id' not in properties:
        raise HTTPException(status_code=400, detail="_id is required")

    # Create entity
    try:
        queries.create_entity(label, properties)
        return RedirectResponse(url=f"/entities/{label}", status_code=303)
    except Exception as e:
        logger.error(f"Failed to create entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/entities/{label}/{entity_id}/edit", response_class=HTMLResponse)
async def edit_entity_form(request: Request, label: str, entity_id: str):
    """Edit form for an entity."""
    queries = get_queries()
    discovery = get_discovery()

    # Get entity
    entity = queries.get_entity_by_id(label, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Get relationships
    relationships = discovery.get_entity_relationships(label, entity_id)

    # Group properties
    grouped_props = group_properties(entity)
    sorted_props = sort_groups(grouped_props)

    # Get display name
    display_name = get_display_name_with_brand(entity, relationships, label)

    return templates.TemplateResponse("entity_edit.html", {
        "request": request,
        "label": label,
        "label_human": humanize_label(label),
        "entity": entity,
        "entity_id": entity_id,
        "display_name": display_name,
        "grouped_properties": sorted_props,
        "relationships": relationships
    })

@app.post("/entities/{label}/{entity_id}/edit")
async def update_entity(request: Request, label: str, entity_id: str):
    """Update an entity."""
    queries = get_queries()

    # Get form data
    form_data = await request.form()
    properties = {}

    for key, value in form_data.items():
        if key.startswith('_') and key != '_id':
            continue

        # Convert value based on property type
        converted_value = convert_value(key, value)

        # Validate
        is_valid, error = validate_value(key, converted_value)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        properties[key] = converted_value

    # Update entity
    try:
        queries.update_entity(label, entity_id, properties)
        return RedirectResponse(url=f"/entities/{label}/{entity_id}", status_code=303)
    except Exception as e:
        logger.error(f"Failed to update entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/entities/{label}/{entity_id}", response_class=HTMLResponse)
async def view_entity(request: Request, label: str, entity_id: str):
    """Detail view for a specific entity."""
    queries = get_queries()
    discovery = get_discovery()

    # Get entity
    entity = queries.get_entity_by_id(label, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Get relationships
    relationships = discovery.get_entity_relationships(label, entity_id)

    # Group properties
    grouped_props = group_properties(entity)
    sorted_props = sort_groups(grouped_props)

    # Get display name with brand
    display_name = get_display_name_with_brand(entity, relationships, label)

    # Check if this is a supporting entity (few properties)
    # If so, get all related entities grouped by type
    related_by_type = {}
    is_supporting_entity = len(entity) <= 5  # Supporting entities typically have few properties

    if is_supporting_entity and relationships:
        # Group related entities by their label
        for rel in relationships:
            if rel['direction'] == 'incoming':  # Things that point to this entity
                rel_label = rel['labels'][0]
                if rel_label not in related_by_type:
                    related_by_type[rel_label] = []
                related_by_type[rel_label].append(rel)

    return templates.TemplateResponse("entity_detail.html", {
        "request": request,
        "label": label,
        "label_human": humanize_label(label),
        "entity": entity,
        "entity_id": entity_id,
        "display_name": display_name,
        "grouped_properties": sorted_props,
        "relationships": relationships,
        "related_by_type": related_by_type,
        "is_supporting_entity": is_supporting_entity
    })

@app.post("/entities/{label}/{entity_id}/delete")
async def delete_entity(label: str, entity_id: str):
    """Delete an entity."""
    queries = get_queries()

    try:
        queries.delete_entity(label, entity_id)
        return RedirectResponse(url=f"/entities/{label}", status_code=303)
    except Exception as e:
        logger.error(f"Failed to delete entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: Optional[str] = None):
    """Global search."""
    if not q:
        return templates.TemplateResponse("search.html", {
            "request": request,
            "query": "",
            "results": []
        })

    queries = get_queries()
    results = queries.search_entities(q)

    return templates.TemplateResponse("search.html", {
        "request": request,
        "query": q,
        "results": results
    })

@app.get("/api/schema")
async def get_schema():
    """API endpoint for schema information."""
    discovery = get_discovery()
    return discovery.get_all_schema_info()

@app.get("/api/entity-types")
async def get_entity_types():
    """API endpoint for entity types (node labels)."""
    discovery = get_discovery()
    schema = discovery.get_all_schema_info()

    # Combine product types and supporting entities
    entity_types = []
    for label in schema['product_types']:
        entity_types.append({
            'label': label,
            'type': 'product',
            'count': schema.get('counts', {}).get(label, 0)
        })

    for label in schema['supporting_entities']:
        entity_types.append({
            'label': label,
            'type': 'supporting',
            'count': schema.get('counts', {}).get(label, 0)
        })

    return {'entity_types': entity_types}

@app.get("/api/graph/relationships")
async def get_relationship_types():
    """API endpoint for relationship types."""
    from .db.connection import get_connection
    conn = get_connection()

    query = """
    CALL db.relationshipTypes() YIELD relationshipType
    RETURN relationshipType
    ORDER BY relationshipType
    """

    try:
        results = conn.execute_query(query)
        rel_types = [record['relationshipType'] for record in results]
        return {'relationships': rel_types}
    except Exception as e:
        logger.error(f"Error fetching relationship types: {e}")
        return {'relationships': []}

# Multilingual / Localization API Endpoints

@app.get("/api/locales")
async def get_locales():
    """
    Get list of supported locales.

    Returns:
        Dictionary with list of supported locales, default locale, and total count
    """
    from .utils.locales import get_all_locales, DEFAULT_LOCALE

    locales = get_all_locales()

    return {
        'locales': locales,
        'default_locale': DEFAULT_LOCALE,
        'total_count': len(locales)
    }

@app.get("/api/schema/{entity_type}")
async def get_schema_for_locale(
    entity_type: str,
    locale: Optional[str] = None
):
    """
    Get property schema for an entity type with localized labels.

    Args:
        entity_type: Entity type (e.g., 'Laptop', 'Smartphone')
        locale: Locale code (e.g., 'es-ES', 'fr'). Defaults to 'en' if not provided

    Returns:
        Schema with localized property names

    Example:
        GET /api/schema/Laptop?locale=es-ES
    """
    from .db.localization import get_localization_queries
    from .db.connection import get_connection
    from .utils.locales import normalize_locale

    # Normalize locale (will default to 'en' if None or unsupported)
    normalized_locale = normalize_locale(locale)

    try:
        # Get localization queries instance
        conn = get_connection()
        localization = get_localization_queries(conn)

        # Get schema
        result = localization.get_schema_for_locale(entity_type, normalized_locale)

        # Add total count
        result['total_properties'] = len(result['properties'])

        return result

    except Exception as e:
        logger.error(f"Error getting schema for locale: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve schema: {str(e)}"
        )

@app.get("/api/{entity_type}/{entity_id}")
async def get_entity_localized(
    entity_type: str,
    entity_id: str,
    locale: Optional[str] = None
):
    """
    Get an entity with localized property names.

    Args:
        entity_type: Entity type (e.g., 'Laptop', 'Smartphone')
        entity_id: Entity identifier
        locale: Locale code (e.g., 'es-ES', 'fr'). Defaults to 'en' if not provided

    Returns:
        Entity data with localized property names

    Example:
        GET /api/Laptop/ASUS-model?locale=fr
    """
    from .db.localization import get_localization_queries
    from .db.connection import get_connection
    from .utils.locales import normalize_locale
    from .utils.display import get_entity_id as find_id_property

    # Normalize locale
    normalized_locale = normalize_locale(locale)

    try:
        # Get localization queries instance
        conn = get_connection()
        localization = get_localization_queries(conn)

        # Try to find the entity with different ID properties
        # Common ID properties in priority order
        id_properties = ['product_model', '_id', 'id', 'name', 'model', 'code']

        result = None
        for id_prop in id_properties:
            try:
                result = localization.get_entity_with_localized_properties(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    locale=normalized_locale,
                    id_property=id_prop
                )
                if result:
                    break
            except Exception:
                continue

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Entity not found: {entity_type} with id '{entity_id}'"
            )

        # Add total count
        result['total_properties'] = len(result['properties'])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting entity with localized properties: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve entity: {str(e)}"
        )

@app.get("/api/translation-coverage/{entity_type}")
async def get_translation_coverage(entity_type: str):
    """
    Get translation coverage report for an entity type.

    Shows which properties have translations in which locales and identifies gaps.

    Args:
        entity_type: Entity type (e.g., 'Laptop', 'Smartphone')

    Returns:
        Translation coverage report

    Example:
        GET /api/translation-coverage/Laptop
    """
    from .db.localization import get_localization_queries
    from .db.connection import get_connection

    try:
        # Get localization queries instance
        conn = get_connection()
        localization = get_localization_queries(conn)

        # Get coverage report
        result = localization.get_translation_coverage(entity_type)

        return result

    except Exception as e:
        logger.error(f"Error getting translation coverage: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve translation coverage: {str(e)}"
        )

# Graph Visualization Routes

@app.get("/graph", response_class=HTMLResponse)
async def graph_view(request: Request):
    """Graph visualization page."""
    discovery = get_discovery()
    schema = discovery.get_all_schema_info()

    return templates.TemplateResponse("graph.html", {
        "request": request,
        "schema": schema
    })

@app.get("/api/graph/explore")
async def explore_graph(
    label: Optional[str] = None,
    entity_id: Optional[str] = None,
    depth: int = 1,
    limit: int = 50
):
    """
    Get graph data for visualization.

    If label and entity_id provided: Start from that entity and expand
    Otherwise: Get a sample of the graph
    """
    from .db.connection import get_connection
    conn = get_connection()

    nodes = []
    edges = []
    seen_nodes = set()
    seen_edges = set()

    try:
        if label and entity_id:
            # Start from specific entity - simplified query
            id_properties = ['_id', 'id', 'name', 'model', 'code']
            results = None

            for id_prop in id_properties:
                query = f"""
                MATCH (start:{label} {{{id_prop}: $entity_id}})
                OPTIONAL MATCH (start)-[r]-(connected)
                RETURN start, r, connected
                LIMIT $limit
                """
                try:
                    results = conn.execute_query(query, {
                        'entity_id': entity_id,
                        'limit': limit
                    })
                    if results:
                        break
                except Exception as e:
                    logger.error(f"Error with property {id_prop}: {e}")
                    continue

            if not results:
                # Return empty graph
                return {'nodes': [], 'edges': []}

            # Process results
            for record in results:
                # Add start node (only once)
                if 'start' in record and record['start']:
                    start_node = dict(record['start'])
                    node_id = get_entity_id(start_node)[1]

                    if node_id not in seen_nodes:
                        # Get labels safely
                        try:
                            node_type = label  # Use the label parameter as type
                        except:
                            node_type = 'Unknown'

                        nodes.append({
                            'id': node_id,
                            'label': get_display_name(start_node, label),
                            'type': node_type,
                            'properties': start_node
                        })
                        seen_nodes.add(node_id)

                # Add connected node if exists
                if 'connected' in record and record['connected']:
                    connected_node = dict(record['connected'])
                    connected_id = get_entity_id(connected_node)[1]

                    if connected_id not in seen_nodes:
                        # Get connected node labels
                        try:
                            # Try to get labels from the node object
                            connected_labels = []
                            if hasattr(record['connected'], 'labels'):
                                connected_labels = list(record['connected'].labels)
                            connected_type = connected_labels[0] if connected_labels else 'Unknown'
                        except:
                            connected_type = 'Unknown'

                        nodes.append({
                            'id': connected_id,
                            'label': get_display_name(connected_node, connected_type),
                            'type': connected_type,
                            'properties': connected_node
                        })
                        seen_nodes.add(connected_id)

                    # Add edge
                    if 'r' in record and record['r']:
                        rel = record['r']
                        start_node = dict(record['start'])
                        start_id = get_entity_id(start_node)[1]

                        try:
                            rel_type = rel.type
                        except:
                            rel_type = 'RELATED_TO'

                        edge_id = f"{start_id}-{rel_type}-{connected_id}"
                        if edge_id not in seen_edges:
                            edges.append({
                                'id': edge_id,
                                'source': start_id,
                                'target': connected_id,
                                'label': rel_type,
                                'type': rel_type
                            })
                            seen_edges.add(edge_id)

        else:
            # Get a sample of the graph - much simpler query
            query = """
            MATCH (n)
            WITH n
            LIMIT $limit
            OPTIONAL MATCH (n)-[r]-(m)
            WITH n, r, m
            LIMIT $limit * 3
            RETURN n, r, m
            """
            results = conn.execute_query(query, {'limit': limit})

            for record in results:
                # Add node n
                if 'n' in record and record['n']:
                    node = dict(record['n'])
                    node_id = get_entity_id(node)[1]

                    if node_id not in seen_nodes:
                        # Get node labels
                        try:
                            if hasattr(record['n'], 'labels'):
                                node_labels = list(record['n'].labels)
                                node_type = node_labels[0] if node_labels else 'Unknown'
                            else:
                                node_type = 'Unknown'
                        except:
                            node_type = 'Unknown'

                        nodes.append({
                            'id': node_id,
                            'label': get_display_name(node, node_type),
                            'type': node_type,
                            'properties': node
                        })
                        seen_nodes.add(node_id)

                # Add node m
                if 'm' in record and record['m']:
                    m_node = dict(record['m'])
                    m_id = get_entity_id(m_node)[1]

                    if m_id not in seen_nodes:
                        try:
                            if hasattr(record['m'], 'labels'):
                                m_labels = list(record['m'].labels)
                                m_type = m_labels[0] if m_labels else 'Unknown'
                            else:
                                m_type = 'Unknown'
                        except:
                            m_type = 'Unknown'

                        nodes.append({
                            'id': m_id,
                            'label': get_display_name(m_node, m_type),
                            'type': m_type,
                            'properties': m_node
                        })
                        seen_nodes.add(m_id)

                # Add relationship
                if 'r' in record and record['r'] and 'n' in record and 'm' in record:
                    node = dict(record['n'])
                    m_node = dict(record['m'])
                    node_id = get_entity_id(node)[1]
                    m_id = get_entity_id(m_node)[1]

                    try:
                        rel_type = record['r'].type
                    except:
                        rel_type = 'RELATED_TO'

                    edge_id = f"{node_id}-{rel_type}-{m_id}"
                    if edge_id not in seen_edges:
                        edges.append({
                            'id': edge_id,
                            'source': node_id,
                            'target': m_id,
                            'label': rel_type,
                            'type': rel_type
                        })
                        seen_edges.add(edge_id)

    except Exception as e:
        logger.error(f"Error in explore_graph: {e}")
        import traceback
        traceback.print_exc()
        # Return empty graph on error
        return {'nodes': [], 'edges': []}

    return {
        'nodes': nodes,
        'edges': edges
    }

@app.get("/api/graph/expand/{label}/{entity_id}")
async def expand_node(label: str, entity_id: str, depth: int = 1):
    """Expand a specific node to show its connections."""
    return await explore_graph(label=label, entity_id=entity_id, depth=depth, limit=100)

# Property Schema Management API Endpoints

@app.get("/api/properties")
async def list_properties(
    entity_type: Optional[str] = None,
    translation_status: Optional[str] = None,
    search: Optional[str] = None
):
    """
    List all property definitions with optional filters.

    Args:
        entity_type: Filter by entity type (e.g., 'Laptop')
        translation_status: Filter by translation status ('complete', 'incomplete', 'none')
        search: Search in property keys

    Returns:
        List of properties with translation counts and status

    Example:
        GET /api/properties?entity_type=Laptop&translation_status=incomplete
    """
    from .db.property_schema import get_property_schema_queries
    from .utils.locales import get_all_locales

    try:
        queries = get_property_schema_queries()
        expected_locale_count = len(get_all_locales())

        properties = queries.get_all_properties(
            entity_type=entity_type,
            translation_status=translation_status,
            search=search,
            expected_locale_count=expected_locale_count
        )

        return {
            "properties": properties,
            "total_count": len(properties),
            "entity_type": entity_type
        }

    except Exception as e:
        logger.error(f"Error listing properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/properties/{entity_type}/{property_key}")
async def get_property_detail(entity_type: str, property_key: str):
    """
    Get a single property definition with all translations.

    Args:
        entity_type: Entity type (e.g., 'Laptop')
        property_key: Property key (e.g., 'screen_size')

    Returns:
        Property definition with all translations

    Example:
        GET /api/properties/Laptop/screen_size
    """
    from .db.property_schema import get_property_schema_queries

    try:
        queries = get_property_schema_queries()
        property_def = queries.get_property(entity_type, property_key)

        if not property_def:
            raise HTTPException(
                status_code=404,
                detail=f"Property not found: {entity_type}.{property_key}"
            )

        return property_def

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/properties")
async def create_property(request: Request):
    """
    Create a new property definition with optional translations.

    Request body should match CreatePropertyRequest model.

    Returns:
        Created property definition

    Example:
        POST /api/properties
        {
            "property_key": "price",
            "entity_type": "Laptop",
            "data_type": "FLOAT",
            "unit": "USD",
            "translations": [
                {"locale": "en", "label": "Price"},
                {"locale": "es-ES", "label": "Precio"}
            ]
        }
    """
    from .db.property_schema import get_property_schema_queries
    from .models.property_schema import CreatePropertyRequest

    try:
        # Parse and validate request
        data = await request.json()
        create_request = CreatePropertyRequest(**data)

        queries = get_property_schema_queries()

        # Create property
        property_def = queries.create_property(
            property_key=create_request.property_key,
            entity_type=create_request.entity_type,
            data_type=create_request.data_type,
            unit=create_request.unit,
            translations=create_request.translations.dict() if create_request.translations else None
        )

        return {
            "success": True,
            "property": property_def
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/properties/{entity_type}/{property_key}")
async def update_property_metadata(
    entity_type: str,
    property_key: str,
    request: Request
):
    """
    Update property metadata (data_type, unit).

    Args:
        entity_type: Entity type
        property_key: Property key

    Request body should match UpdatePropertyRequest model.

    Example:
        PUT /api/properties/Laptop/screen_size
        {
            "data_type": "FLOAT",
            "unit": "inches"
        }
    """
    from .db.property_schema import get_property_schema_queries
    from .models.property_schema import UpdatePropertyRequest

    try:
        # Parse and validate request
        data = await request.json()
        update_request = UpdatePropertyRequest(**data)

        queries = get_property_schema_queries()

        # Update property
        success = queries.update_property(
            entity_type=entity_type,
            property_key=property_key,
            data_type=update_request.data_type,
            unit=update_request.unit
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Property not found: {entity_type}.{property_key}"
            )

        # Get updated property
        property_def = queries.get_property(entity_type, property_key)

        return {
            "success": True,
            "property": property_def
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/properties/{entity_type}/{property_key}")
async def delete_property_definition(entity_type: str, property_key: str):
    """
    Delete a property definition and all its translations.

    Args:
        entity_type: Entity type
        property_key: Property key

    Example:
        DELETE /api/properties/Laptop/old_property
    """
    from .db.property_schema import get_property_schema_queries

    try:
        queries = get_property_schema_queries()
        success = queries.delete_property(entity_type, property_key)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Property not found: {entity_type}.{property_key}"
            )

        return {
            "success": True,
            "message": f"Property {entity_type}.{property_key} deleted"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/properties/{entity_type}/{property_key}/translations/{locale}")
async def set_property_translation(
    entity_type: str,
    property_key: str,
    locale: str,
    request: Request
):
    """
    Add or update a single translation for a property.

    Args:
        entity_type: Entity type
        property_key: Property key
        locale: Locale code (e.g., 'es-ES')

    Request body should contain 'label' field.

    Example:
        PUT /api/properties/Laptop/price/translations/es-ES
        {
            "label": "Precio"
        }
    """
    from .db.property_schema import get_property_schema_queries
    from .utils.locales import normalize_locale

    try:
        # Validate locale
        normalized_locale = normalize_locale(locale)
        if not normalized_locale:
            raise HTTPException(status_code=400, detail=f"Unsupported locale: {locale}")

        # Parse request
        data = await request.json()
        label = data.get('label')

        if not label:
            raise HTTPException(status_code=400, detail="Missing 'label' field")

        queries = get_property_schema_queries()
        success = queries.set_translation(
            entity_type=entity_type,
            property_key=property_key,
            locale=normalized_locale,
            label=label
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Property not found: {entity_type}.{property_key}"
            )

        return {
            "success": True,
            "message": f"Translation set for {normalized_locale}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting translation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/properties/{entity_type}/{property_key}/translations/bulk")
async def set_bulk_translations(
    entity_type: str,
    property_key: str,
    request: Request
):
    """
    Update multiple translations at once for a property.

    Args:
        entity_type: Entity type
        property_key: Property key

    Request body should contain 'translations' object mapping locale to label.

    Example:
        POST /api/properties/Laptop/price/translations/bulk
        {
            "translations": {
                "en": "Price",
                "es-ES": "Precio",
                "fr": "Prix"
            }
        }
    """
    from .db.property_schema import get_property_schema_queries

    try:
        # Parse request
        data = await request.json()
        translations = data.get('translations', {})

        if not translations:
            raise HTTPException(status_code=400, detail="Missing 'translations' field")

        queries = get_property_schema_queries()
        success = queries.set_translations_bulk(
            entity_type=entity_type,
            property_key=property_key,
            translations=translations
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Property not found: {entity_type}.{property_key}"
            )

        return {
            "success": True,
            "message": f"Updated {len(translations)} translations"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting bulk translations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/properties/{entity_type}/{property_key}/translations/{locale}")
async def delete_property_translation(
    entity_type: str,
    property_key: str,
    locale: str
):
    """
    Delete a specific translation for a property.

    Args:
        entity_type: Entity type
        property_key: Property key
        locale: Locale code

    Example:
        DELETE /api/properties/Laptop/price/translations/es-ES
    """
    from .db.property_schema import get_property_schema_queries

    try:
        queries = get_property_schema_queries()
        success = queries.delete_translation(entity_type, property_key, locale)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Translation not found: {entity_type}.{property_key} ({locale})"
            )

        return {
            "success": True,
            "message": f"Translation deleted for {locale}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting translation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/properties/discover/{entity_type}")
async def discover_undocumented_properties(entity_type: str, limit: int = 10):
    """
    Discover properties that exist in the data but don't have PropertyDefinition nodes.

    Args:
        entity_type: Entity type to scan
        limit: Maximum number of sample values per property

    Returns:
        List of undocumented properties with sample values and suggested data types

    Example:
        GET /api/properties/discover/Laptop?limit=5
    """
    from .db.property_schema import get_property_schema_queries

    try:
        queries = get_property_schema_queries()
        result = queries.discover_undocumented_properties(entity_type, sample_limit=limit)

        return result

    except Exception as e:
        logger.error(f"Error discovering properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/properties/statistics")
async def get_property_statistics():
    """
    Get overall property statistics across all entity types.

    Returns:
        Statistics including total properties, translation counts per entity type

    Example:
        GET /api/properties/statistics
    """
    from .db.property_schema import get_property_schema_queries
    from .utils.locales import get_all_locales

    try:
        queries = get_property_schema_queries()
        expected_locale_count = len(get_all_locales())

        stats = queries.get_statistics(expected_locale_count)

        return stats

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/properties/coverage/{entity_type}")
async def get_property_coverage(entity_type: str):
    """
    Get translation coverage report for a specific entity type.

    Shows which properties have translations in which locales.

    Args:
        entity_type: Entity type to analyze

    Returns:
        Coverage report with per-property breakdown

    Example:
        GET /api/properties/coverage/Laptop
    """
    from .db.property_schema import get_property_schema_queries
    from .utils.locales import get_all_locales

    try:
        queries = get_property_schema_queries()
        expected_locales = [loc['code'] for loc in get_all_locales()]

        coverage = queries.get_coverage_report(entity_type, expected_locales)

        return coverage

    except Exception as e:
        logger.error(f"Error getting coverage report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/properties/entity-types")
async def get_property_entity_types():
    """
    Get list of entity types that have property definitions.

    Returns:
        List of entity types with property counts

    Example:
        GET /api/properties/entity-types
    """
    from .db.property_schema import get_property_schema_queries

    try:
        queries = get_property_schema_queries()
        entity_types = queries.get_entity_types()

        return {
            "entity_types": entity_types,
            "total_count": len(entity_types)
        }

    except Exception as e:
        logger.error(f"Error getting entity types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/properties/import")
async def import_properties(request: Request):
    """
    Import property definitions from JSON or CSV format.

    Request body should contain:
    - format: 'json' or 'csv'
    - data: JSON array or CSV content
    - merge: true to merge with existing, false to replace (optional, default: true)

    JSON format:
    [
        {
            "property_key": "price",
            "entity_type": "Laptop",
            "data_type": "FLOAT",
            "unit": "USD",
            "translations": {
                "en": "Price",
                "es-ES": "Precio"
            }
        }
    ]

    CSV format:
    property_key,entity_type,data_type,unit,en,es-ES,fr
    price,Laptop,FLOAT,USD,Price,Precio,Prix

    Example:
        POST /api/properties/import
    """
    from .db.property_schema import get_property_schema_queries
    import json
    import csv
    import io

    try:
        data = await request.json()
        format_type = data.get('format', 'json')
        import_data = data.get('data', '')
        merge = data.get('merge', True)

        if not import_data:
            raise HTTPException(status_code=400, detail="Missing 'data' field")

        queries = get_property_schema_queries()
        created = 0
        updated = 0
        errors = []

        if format_type == 'json':
            # Parse JSON
            try:
                properties = json.loads(import_data) if isinstance(import_data, str) else import_data
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

            if not isinstance(properties, list):
                raise HTTPException(status_code=400, detail="JSON data must be an array")

            # Process each property
            for prop in properties:
                try:
                    property_key = prop.get('property_key')
                    entity_type = prop.get('entity_type')
                    data_type = prop.get('data_type', 'STRING')
                    unit = prop.get('unit')
                    translations = prop.get('translations', {})

                    if not property_key or not entity_type:
                        errors.append(f"Missing property_key or entity_type in: {prop}")
                        continue

                    # Check if property exists
                    existing = queries.get_property(entity_type, property_key)

                    if existing and not merge:
                        # Skip if not merging
                        continue
                    elif existing:
                        # Update existing
                        queries.update_property(entity_type, property_key, data_type, unit)
                        if translations:
                            queries.set_translations_bulk(entity_type, property_key, translations)
                        updated += 1
                    else:
                        # Create new
                        translation_list = [{"locale": k, "label": v} for k, v in translations.items()]
                        queries.create_property(
                            property_key=property_key,
                            entity_type=entity_type,
                            data_type=data_type,
                            unit=unit,
                            translations=translation_list if translation_list else None
                        )
                        created += 1

                except Exception as e:
                    errors.append(f"Error processing {prop.get('property_key', 'unknown')}: {str(e)}")

        elif format_type == 'csv':
            # Parse CSV
            try:
                csv_file = io.StringIO(import_data)
                reader = csv.DictReader(csv_file)

                # Get column names
                if not reader.fieldnames:
                    raise HTTPException(status_code=400, detail="CSV has no headers")

                # Expected columns
                required_cols = ['property_key', 'entity_type']
                if not all(col in reader.fieldnames for col in required_cols):
                    raise HTTPException(
                        status_code=400,
                        detail=f"CSV must have columns: {', '.join(required_cols)}"
                    )

                # Get locale columns (any column not in standard fields)
                standard_fields = {'property_key', 'entity_type', 'data_type', 'unit'}
                locale_cols = [col for col in reader.fieldnames if col not in standard_fields]

                # Process each row
                for row in reader:
                    try:
                        property_key = row.get('property_key', '').strip()
                        entity_type = row.get('entity_type', '').strip()
                        data_type = row.get('data_type', 'STRING').strip() or 'STRING'
                        unit = row.get('unit', '').strip() or None

                        if not property_key or not entity_type:
                            errors.append(f"Missing property_key or entity_type in row: {row}")
                            continue

                        # Build translations from locale columns
                        translations = {}
                        for locale_col in locale_cols:
                            label = row.get(locale_col, '').strip()
                            if label:
                                translations[locale_col] = label

                        # Check if property exists
                        existing = queries.get_property(entity_type, property_key)

                        if existing and not merge:
                            continue
                        elif existing:
                            queries.update_property(entity_type, property_key, data_type, unit)
                            if translations:
                                queries.set_translations_bulk(entity_type, property_key, translations)
                            updated += 1
                        else:
                            translation_list = [{"locale": k, "label": v} for k, v in translations.items()]
                            queries.create_property(
                                property_key=property_key,
                                entity_type=entity_type,
                                data_type=data_type,
                                unit=unit,
                                translations=translation_list if translation_list else None
                            )
                            created += 1

                    except Exception as e:
                        errors.append(f"Error processing row {row.get('property_key', 'unknown')}: {str(e)}")

            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid CSV: {str(e)}")

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format_type}")

        return {
            "success": True,
            "created": created,
            "updated": updated,
            "errors": errors,
            "total_processed": created + updated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/properties/export")
async def export_properties(
    format: str = 'json',
    entity_type: Optional[str] = None
):
    """
    Export property definitions to JSON or CSV format.

    Args:
        format: Export format ('json' or 'csv')
        entity_type: Optional filter by entity type

    Returns:
        Exported data in requested format

    Example:
        GET /api/properties/export?format=json
        GET /api/properties/export?format=csv&entity_type=Laptop
    """
    from .db.property_schema import get_property_schema_queries
    from .utils.locales import get_all_locales
    import json
    import csv
    import io

    try:
        if format not in ['json', 'csv']:
            raise HTTPException(status_code=400, detail="format must be 'json' or 'csv'")

        queries = get_property_schema_queries()

        # Get all properties with details
        properties = queries.get_all_properties(
            entity_type=entity_type,
            expected_locale_count=len(get_all_locales())
        )

        # Enrich with full translation details
        export_data = []
        for prop in properties:
            # Get full property details including translations
            full_prop = queries.get_property(prop['entity_type'], prop['property_key'])
            if full_prop:
                export_data.append(full_prop)

        if format == 'json':
            # Export as JSON
            output = json.dumps(export_data, indent=2, ensure_ascii=False)

            return {
                "format": "json",
                "data": output,
                "total_properties": len(export_data)
            }

        elif format == 'csv':
            # Export as CSV
            # Get all locales
            locales = [loc['code'] for loc in get_all_locales()]

            # Build CSV
            output = io.StringIO()
            fieldnames = ['property_key', 'entity_type', 'data_type', 'unit'] + locales
            writer = csv.DictWriter(output, fieldnames=fieldnames)

            writer.writeheader()

            for prop in export_data:
                row = {
                    'property_key': prop['property_key'],
                    'entity_type': prop['entity_type'],
                    'data_type': prop.get('data_type', 'STRING'),
                    'unit': prop.get('unit', '')
                }

                # Add translations
                for trans in prop.get('translations', []):
                    locale = trans['locale']
                    if locale in locales:
                        row[locale] = trans['label']

                writer.writerow(row)

            csv_content = output.getvalue()

            return {
                "format": "csv",
                "data": csv_content,
                "total_properties": len(export_data)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Property Schema Editor Web Routes

@app.get("/schema", response_class=HTMLResponse)
async def schema_dashboard(request: Request):
    """Property schema editor dashboard."""
    return templates.TemplateResponse("schema_dashboard.html", {
        "request": request
    })


@app.get("/schema/properties", response_class=HTMLResponse)
async def schema_properties_list(request: Request):
    """Property list view with filters."""
    return templates.TemplateResponse("schema_properties.html", {
        "request": request
    })


@app.get("/schema/properties/{entity_type}/{property_key}", response_class=HTMLResponse)
async def schema_property_detail(request: Request, entity_type: str, property_key: str):
    """Property detail and edit page."""
    return templates.TemplateResponse("schema_property_detail.html", {
        "request": request,
        "entity_type": entity_type,
        "property_key": property_key
    })


@app.get("/schema/import", response_class=HTMLResponse)
async def schema_import_page(request: Request):
    """Bulk import page."""
    return templates.TemplateResponse("schema_import.html", {
        "request": request
    })


@app.get("/schema/discover", response_class=HTMLResponse)
async def schema_discover_page(request: Request):
    """Property discovery page."""
    return templates.TemplateResponse("schema_discover.html", {
        "request": request
    })


# Chatbot / GraphRAG API Endpoints

@app.post("/api/chatbot/settings")
async def save_chatbot_settings(request: Request):
    """
    Save LLM and prompt settings for the chatbot.

    Request body should contain:
    - llm_settings: LLM provider configuration
    - prompt_config: System prompt configuration

    Example:
        POST /api/chatbot/settings
        {
            "llm_settings": {
                "provider": "openai",
                "api_key": "sk-...",
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 2000
            },
            "prompt_config": {
                "custom_prompt": null,
                "include_schema": true,
                "include_examples": true
            }
        }
    """
    from .models.chatbot import SaveSettingsRequest
    from .services.llm_service import get_llm_service

    try:
        data = await request.json()
        settings_request = SaveSettingsRequest(**data)

        # Initialize/update LLM service
        service = get_llm_service(
            settings=settings_request.llm_settings,
            prompt_config=settings_request.prompt_config
        )

        if service is None:
            raise HTTPException(status_code=500, detail="Failed to initialize LLM service")

        return {
            "success": True,
            "message": "Chatbot settings saved successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving chatbot settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chatbot/chat")
async def chat_with_graph(request: Request):
    """
    Send a message to the chatbot and get a response.

    The chatbot will:
    1. Convert the question to a Cypher query
    2. Execute the query on the graph
    3. Format the results as a natural language response

    Request body should contain:
    - message: User's question
    - conversation_id: Optional conversation ID for multi-turn chat

    Example:
        POST /api/chatbot/chat
        {
            "message": "What laptops do we have with more than 16GB RAM?",
            "conversation_id": "conv_123"
        }
    """
    from .models.chatbot import ChatRequest, ChatResponse
    from .services.llm_service import get_llm_service
    from .db.discovery import get_discovery
    from .db.connection import get_connection
    from datetime import datetime
    import uuid

    try:
        data = await request.json()
        chat_request = ChatRequest(**data)

        # Get LLM service
        llm_service = get_llm_service()
        if llm_service is None:
            raise HTTPException(
                status_code=400,
                detail="Chatbot not configured. Please configure LLM settings first."
            )

        # Get graph schema
        discovery = get_discovery()
        schema = discovery.get_all_schema_info()

        # Generate Cypher query
        cypher_query = await llm_service.generate_cypher(
            question=chat_request.message,
            graph_schema=schema
        )

        logger.info(f"Generated Cypher: {cypher_query}")

        # Execute query
        conn = get_connection()
        try:
            results = conn.execute_query(cypher_query)
            # Convert results to dictionaries
            results_list = [dict(record) for record in results]
        except Exception as e:
            logger.error(f"Error executing Cypher query: {e}")
            # Return error message
            return ChatResponse(
                message=f"I encountered an error while querying the database: {str(e)}",
                cypher_query=cypher_query,
                query_results=[],
                conversation_id=chat_request.conversation_id or str(uuid.uuid4()),
                timestamp=datetime.now()
            )

        # Format response
        response_text = await llm_service.format_response(
            question=chat_request.message,
            cypher_query=cypher_query,
            results=results_list
        )

        return ChatResponse(
            message=response_text,
            cypher_query=cypher_query,
            query_results=results_list,
            conversation_id=chat_request.conversation_id or str(uuid.uuid4()),
            timestamp=datetime.now()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chatbot/test-connection")
async def test_llm_connection():
    """
    Test the LLM connection with a simple query.

    Returns success if the LLM is configured and responding.
    """
    from .services.llm_service import get_llm_service

    try:
        llm_service = get_llm_service()
        if llm_service is None:
            raise HTTPException(
                status_code=400,
                detail="Chatbot not configured. Please configure LLM settings first."
            )

        # Test with a simple Cypher generation
        test_schema = {
            'labels': ['Test'],
            'relationship_types': []
        }

        test_response = await llm_service.generate_cypher(
            question="Show me all items",
            graph_schema=test_schema
        )

        return {
            "success": True,
            "message": "LLM connection successful",
            "provider": llm_service.settings.provider.value,
            "model": llm_service.settings.model,
            "test_response": test_response[:100]  # First 100 chars
        }

    except Exception as e:
        logger.error(f"Error testing LLM connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request):
    """Chatbot interface page."""
    return templates.TemplateResponse("chatbot.html", {
        "request": request
    })


# Pattern Management Routes

@app.get("/patterns", response_class=HTMLResponse)
async def patterns_page(request: Request):
    """Pattern library page."""
    from .db.patterns import get_pattern_manager
    pattern_mgr = get_pattern_manager()

    patterns = pattern_mgr.list_patterns(limit=50)

    return templates.TemplateResponse("patterns.html", {
        "request": request,
        "patterns": patterns
    })

@app.post("/api/patterns/save")
async def save_pattern(request: Request):
    """Save a new pattern."""
    from .db.patterns import get_pattern_manager
    pattern_mgr = get_pattern_manager()

    data = await request.json()

    try:
        pattern = pattern_mgr.save_pattern(data)
        return {"success": True, "pattern": pattern}
    except Exception as e:
        logger.error(f"Failed to save pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/patterns/list")
async def list_patterns(limit: int = 100, offset: int = 0):
    """List all saved patterns."""
    from .db.patterns import get_pattern_manager
    pattern_mgr = get_pattern_manager()

    patterns = pattern_mgr.list_patterns(limit=limit, offset=offset)
    return {"patterns": patterns}

@app.get("/api/patterns/{pattern_id}")
async def get_pattern(pattern_id: str):
    """Get a single pattern."""
    from .db.patterns import get_pattern_manager
    pattern_mgr = get_pattern_manager()

    pattern = pattern_mgr.get_pattern(pattern_id)
    if pattern:
        return pattern
    raise HTTPException(status_code=404, detail="Pattern not found")

@app.put("/api/patterns/{pattern_id}")
async def update_pattern(pattern_id: str, request: Request):
    """Update a pattern."""
    from .db.patterns import get_pattern_manager
    pattern_mgr = get_pattern_manager()

    data = await request.json()
    pattern = pattern_mgr.update_pattern(pattern_id, data)

    if pattern:
        return {"success": True, "pattern": pattern}
    raise HTTPException(status_code=404, detail="Pattern not found")

@app.delete("/api/patterns/{pattern_id}")
async def delete_pattern(pattern_id: str):
    """Delete a pattern."""
    from .db.patterns import get_pattern_manager
    pattern_mgr = get_pattern_manager()

    success = pattern_mgr.delete_pattern(pattern_id)
    if success:
        return {"success": True}
    raise HTTPException(status_code=404, detail="Pattern not found")

@app.get("/api/patterns/search")
async def search_patterns(q: str):
    """Search patterns."""
    from .db.patterns import get_pattern_manager
    pattern_mgr = get_pattern_manager()

    patterns = pattern_mgr.search_patterns(q)
    return {"patterns": patterns}

@app.post("/api/patterns/{pattern_id}/execute")
async def execute_pattern(pattern_id: str):
    """Execute a saved pattern."""
    from .db.patterns import get_pattern_manager
    pattern_mgr = get_pattern_manager()

    pattern = pattern_mgr.get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    # Execute the Cypher query
    from .db.connection import get_connection
    conn = get_connection()

    try:
        results = conn.execute_query(pattern['cypher_query'])
        return {"success": True, "results": results}
    except Exception as e:
        logger.error(f"Failed to execute pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=config.app_host,
        port=config.app_port,
        reload=config.app_debug
    )
