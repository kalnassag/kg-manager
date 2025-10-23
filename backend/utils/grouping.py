"""Utility functions for grouping properties."""
from typing import Dict, List, Tuple
from collections import defaultdict

def group_properties(properties: Dict[str, any]) -> Dict[str, Dict[str, any]]:
    """
    Group properties by their prefix pattern.

    Returns a dict of groups, each containing properties.

    Example:
    {
        'Product Information': {'product_model': 'EliteBook', ...},
        'Design': {
            'Body': {'design_body_material': 'Aluminum', ...},
            'Keyboard': {'design_keyboard_backlit': True, ...}
        },
        'Technical Specifications': {
            'CPU': {'inside_cpu_model': 'i7-1265U', ...},
            'RAM': {'inside_ram_size': 16, ...}
        }
    }
    """
    groups = defaultdict(lambda: defaultdict(dict))

    # Define group mappings
    group_mappings = {
        'product': ('Product Information', None),
        'design': ('Design & Build', {
            'body': 'Body',
            'keyboard': 'Keyboard',
            'touchpad': 'Touchpad'
        }),
        'inside': ('Technical Specifications', {
            'cpu': 'CPU',
            'ram': 'Memory',
            'gpu': 'Graphics',
            'ssd': 'Storage',
            'wireless': 'Wireless',
            'ports': 'Ports & Connectivity',
            'battery': 'Battery',
            'power': 'Power Supply',
            'security': 'Security',
            'software': 'Software'
        }),
        'display': ('Display', None),
        'camera': ('Camera', None),
        'has': ('Features', None)
    }

    for prop_name, prop_value in properties.items():
        # Skip internal properties except _id
        if prop_name.startswith('_') and prop_name != '_id':
            continue

        parts = prop_name.split('_')

        if len(parts) == 1:
            # No prefix, put in General
            groups['General']['_ungrouped'][prop_name] = prop_value
            continue

        # Get first part (main group)
        main_prefix = parts[0]

        if main_prefix in group_mappings:
            main_group, sub_mappings = group_mappings[main_prefix]

            if sub_mappings and len(parts) > 1:
                # Has sub-groups
                sub_prefix = parts[1]
                if sub_prefix in sub_mappings:
                    sub_group = sub_mappings[sub_prefix]
                    groups[main_group][sub_group][prop_name] = prop_value
                else:
                    # Unknown sub-group, put in main group
                    groups[main_group]['_ungrouped'][prop_name] = prop_value
            else:
                # No sub-groups, put directly in main group
                groups[main_group]['_ungrouped'][prop_name] = prop_value
        else:
            # Unknown prefix, put in General
            groups['General']['_ungrouped'][prop_name] = prop_value

    # Convert defaultdict to regular dict and clean up
    result = {}
    for main_group, sub_groups in groups.items():
        if len(sub_groups) == 1 and '_ungrouped' in sub_groups:
            # No actual sub-groups, flatten
            result[main_group] = dict(sub_groups['_ungrouped'])
        else:
            # Has sub-groups
            result[main_group] = {}
            for sub_group, props in sub_groups.items():
                if sub_group == '_ungrouped':
                    # Add ungrouped items directly to main group
                    for k, v in props.items():
                        result[main_group][k] = v
                else:
                    result[main_group][sub_group] = dict(props)

    return result

def get_property_priority_order() -> List[str]:
    """
    Get the priority order for displaying property groups.

    Returns list of group names in display order.
    """
    return [
        'Product Information',
        'Design & Build',
        'Technical Specifications',
        'Display',
        'Camera',
        'Features',
        'General'
    ]

def sort_groups(grouped_properties: Dict) -> List[Tuple[str, any]]:
    """
    Sort grouped properties by priority order.

    Returns list of (group_name, group_content) tuples.
    """
    priority = get_property_priority_order()
    sorted_groups = []

    # Add groups in priority order
    for group_name in priority:
        if group_name in grouped_properties:
            sorted_groups.append((group_name, grouped_properties[group_name]))

    # Add any remaining groups not in priority list
    for group_name in sorted(grouped_properties.keys()):
        if group_name not in priority:
            sorted_groups.append((group_name, grouped_properties[group_name]))

    return sorted_groups

def is_nested_group(group_content: any) -> bool:
    """
    Check if a group contains sub-groups.

    Returns True if the group has nested dictionaries (sub-groups).
    """
    if not isinstance(group_content, dict):
        return False

    for value in group_content.values():
        if isinstance(value, dict):
            # Check if this dict contains properties (not a property value)
            # A property value dict would be something like {'unit': 'mm', 'value': 15}
            # A sub-group dict would contain multiple key-value pairs where keys are property names
            if any(isinstance(v, (str, int, float, bool, type(None))) for v in value.values()):
                # Might be a nested structure, check if keys look like property names
                if any('_' in k or k.startswith('has_') for k in value.keys()):
                    return True

    return False
