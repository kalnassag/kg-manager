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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=config.app_host,
        port=config.app_port,
        reload=config.app_debug
    )
