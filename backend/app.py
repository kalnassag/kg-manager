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

    if label and entity_id:
        # Start from specific entity
        # Try to find the node with flexible ID
        id_properties = ['_id', 'id', 'name', 'model', 'code']
        node_found = False

        for id_prop in id_properties:
            query = f"""
            MATCH path = (start:{label} {{{id_prop}: $entity_id}})-[r*1..{depth}]-(connected)
            WITH start, r, connected
            LIMIT $limit
            RETURN start, r, connected
            """
            try:
                results = conn.execute_query(query, {
                    'entity_id': entity_id,
                    'limit': limit
                })
                if results:
                    node_found = True
                    break
            except:
                continue

        if not node_found:
            # Fallback: try any property match
            query = f"""
            MATCH path = (start:{label})-[r*1..{depth}]-(connected)
            WHERE any(prop IN keys(start) WHERE toString(start[prop]) = $entity_id)
            WITH start, r, connected
            LIMIT $limit
            RETURN start, r, connected
            """
            results = conn.execute_query(query, {
                'entity_id': entity_id,
                'limit': limit
            })

        # Process results
        seen_nodes = set()
        seen_edges = set()

        for record in results:
            # Add start node
            start_node = dict(record['start'])
            start_labels = list(record['start'].labels)
            node_id = get_entity_id(start_node)[1]

            if node_id not in seen_nodes:
                nodes.append({
                    'id': node_id,
                    'label': get_display_name(start_node, start_labels[0] if start_labels else ''),
                    'type': start_labels[0] if start_labels else 'Unknown',
                    'properties': start_node
                })
                seen_nodes.add(node_id)

            # Add connected node
            connected_node = dict(record['connected'])
            connected_labels = list(record['connected'].labels)
            connected_id = get_entity_id(connected_node)[1]

            if connected_id not in seen_nodes:
                nodes.append({
                    'id': connected_id,
                    'label': get_display_name(connected_node, connected_labels[0] if connected_labels else ''),
                    'type': connected_labels[0] if connected_labels else 'Unknown',
                    'properties': connected_node
                })
                seen_nodes.add(connected_id)

            # Add relationships
            if record['r']:
                for rel_path in record['r']:
                    rel_list = rel_path if isinstance(rel_path, list) else [rel_path]
                    for rel in rel_list:
                        edge_id = f"{node_id}-{rel.type}-{connected_id}"
                        if edge_id not in seen_edges:
                            edges.append({
                                'id': edge_id,
                                'source': node_id,
                                'target': connected_id,
                                'label': rel.type,
                                'type': rel.type
                            })
                            seen_edges.add(edge_id)

    else:
        # Get a sample of the graph
        query = """
        MATCH (n)
        WITH n, rand() as r
        ORDER BY r
        LIMIT $limit
        OPTIONAL MATCH (n)-[rel]-(m)
        RETURN n, collect(distinct {rel: rel, m: m}) as connections
        """
        results = conn.execute_query(query, {'limit': limit})

        seen_nodes = set()
        seen_edges = set()

        for record in results:
            # Add node
            node = dict(record['n'])
            node_labels = list(record['n'].labels)
            node_id = get_entity_id(node)[1]

            if node_id not in seen_nodes:
                nodes.append({
                    'id': node_id,
                    'label': get_display_name(node, node_labels[0] if node_labels else ''),
                    'type': node_labels[0] if node_labels else 'Unknown',
                    'properties': node
                })
                seen_nodes.add(node_id)

            # Add connections
            for conn_data in record['connections']:
                if conn_data['rel'] and conn_data['m']:
                    rel = conn_data['rel']
                    m = conn_data['m']

                    m_dict = dict(m)
                    m_labels = list(m.labels)
                    m_id = get_entity_id(m_dict)[1]

                    if m_id not in seen_nodes:
                        nodes.append({
                            'id': m_id,
                            'label': get_display_name(m_dict, m_labels[0] if m_labels else ''),
                            'type': m_labels[0] if m_labels else 'Unknown',
                            'properties': m_dict
                        })
                        seen_nodes.add(m_id)

                    # Add edge
                    edge_id = f"{node_id}-{rel.type}-{m_id}"
                    if edge_id not in seen_edges:
                        edges.append({
                            'id': edge_id,
                            'source': node_id,
                            'target': m_id,
                            'label': rel.type,
                            'type': rel.type
                        })
                        seen_edges.add(edge_id)

    return {
        'nodes': nodes,
        'edges': edges
    }

@app.get("/api/graph/expand/{label}/{entity_id}")
async def expand_node(label: str, entity_id: str, depth: int = 1):
    """Expand a specific node to show its connections."""
    return await explore_graph(label=label, entity_id=entity_id, depth=depth, limit=100)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=config.app_host,
        port=config.app_port,
        reload=config.app_debug
    )
