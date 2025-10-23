"""Utility functions for computing display names."""
from typing import Dict, Optional, List

def get_display_name(node: Dict, label: str = "") -> str:
    """
    Compute a human-readable display name for a node.

    Priority:
    1. product_model
    2. model
    3. name
    4. version
    5. First string property
    6. _id (formatted)
    """
    if not node:
        return "Unknown"

    # Try priority properties
    priority_props = ['product_model', 'model', 'name', 'version', 'title']
    for prop in priority_props:
        if prop in node and node[prop]:
            return str(node[prop])

    # Try first string property
    for key, value in node.items():
        if key.startswith('_'):
            continue
        if isinstance(value, str) and value.strip():
            return value

    # Fallback to _id
    if '_id' in node:
        return format_id(node['_id'])

    # Last resort
    return f"{label} Entity" if label else "Unknown Entity"

def format_id(id_value: str) -> str:
    """Format an ID value for display."""
    if not id_value:
        return ""

    # If it's a UUID or long string, truncate
    if len(id_value) > 20:
        return f"{id_value[:8]}...{id_value[-8:]}"

    return id_value

def get_display_name_with_brand(node: Dict, relationships: List[Dict] = None, label: str = "") -> str:
    """
    Get display name with brand prefix if available.

    Example: "HP EliteBook 630 G9"
    """
    display_name = get_display_name(node, label)

    if relationships:
        # Look for MADE_BY relationship
        for rel in relationships:
            if rel['type'] == 'MADE_BY' and rel['direction'] == 'outgoing':
                brand_name = get_display_name(rel['node'])
                return f"{brand_name} {display_name}"

    return display_name

def humanize_label(label: str) -> str:
    """
    Convert a label to human-readable format.

    Examples:
    - CPUModel -> CPU Model
    - OperatingSystem -> Operating System
    - Brand -> Brand
    """
    # Handle camelCase and PascalCase
    result = []
    for i, char in enumerate(label):
        if char.isupper() and i > 0:
            # Add space before uppercase if previous char is lowercase
            if label[i-1].islower():
                result.append(' ')
        result.append(char)

    return ''.join(result)

def humanize_property_name(prop_name: str, remove_prefix: bool = True) -> str:
    """
    Convert property name to human-readable format.

    Examples:
    - inside_cpu_clock_speed -> Clock Speed (with remove_prefix=True)
    - inside_cpu_clock_speed -> Inside CPU Clock Speed (with remove_prefix=False)
    - has_fingerprint_reader -> Has Fingerprint Reader
    """
    if not prop_name:
        return ""

    # Skip internal properties
    if prop_name.startswith('_') and prop_name != '_id':
        return prop_name

    parts = prop_name.split('_')

    # Remove prefix if requested (first 1-2 parts)
    if remove_prefix and len(parts) > 2:
        # For properties like inside_cpu_clock_speed, remove 'inside_cpu'
        # For properties like design_body_material, remove 'design_body'
        # For properties like display_size, remove 'display'
        if parts[0] in ['inside', 'design', 'display', 'camera', 'product']:
            if len(parts) > 2 and parts[1] not in ['of', 'and', 'or']:
                parts = parts[2:]
            else:
                parts = parts[1:]
        else:
            # Keep as is
            pass

    # Capitalize each word
    words = [word.capitalize() for word in parts]

    # Special cases for abbreviations
    abbreviations = {
        'Cpu': 'CPU',
        'Gpu': 'GPU',
        'Ram': 'RAM',
        'Ssd': 'SSD',
        'Usb': 'USB',
        'Os': 'OS',
        'Id': 'ID',
        'Hdmi': 'HDMI',
        'Wifi': 'WiFi',
        'Rgb': 'RGB',
        'Fps': 'FPS',
        'Hdr': 'HDR'
    }

    words = [abbreviations.get(word, word) for word in words]

    return ' '.join(words)

def humanize_relationship_type(rel_type: str) -> str:
    """
    Convert relationship type to human-readable format.

    Examples:
    - MADE_BY -> Made By
    - HAS_CPU -> Has CPU
    - BELONGS_TO_FAMILY -> Belongs To Family
    """
    words = rel_type.split('_')
    words = [word.capitalize() for word in words]

    # Special cases
    abbreviations = {
        'Cpu': 'CPU',
        'Gpu': 'GPU',
        'Os': 'OS'
    }

    words = [abbreviations.get(word, word) for word in words]

    return ' '.join(words)
