"""
QSA (Quip Simple Automation) file parser.

Parses .qsa files and converts them to the dictionary format used by the generator.
"""

import re
from typing import Dict, List, Any, Optional
import uuid


def parse_qsa_file(file_path: str, project_prefix: Optional[str] = None) -> Dict[str, Any]:
    """Parse a .qsa file and convert to dictionary format

    Args:
        file_path: Path to the .qsa file
        project_prefix: Optional project prefix from config (e.g., 'cs')
    """

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Remove empty lines and comments
    lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]

    if len(lines) < 2:
        raise ValueError("QSA file must have at least name and description")

    name = lines[0]
    description = lines[1]

    result = {
        'name': name,
        'template_type': 'Extension',
        'agent_type': 'Any',
        'extension': generate_extension_id(name, project_prefix),
        'min_release': '7.6.0.0',
        'var_prefix': generate_var_prefix(name, project_prefix),
        'sys_id': str(uuid.uuid4()).replace('-', ''),
        'common_script': False,
        'always_cancel': True,
        'send_environment': 'Launch',
        'send_variables': 'None',
        'description': description,
        'fields': [],
        'events': [],
        'commands': []
    }

    # First pass: collect all choice fields to resolve indices in conditions
    choice_fields_map = {}
    for line in lines[2:]:
        if ' if ' in line:
            line = line.rsplit(' if ', 1)[0]

        # Extract choice fields (handle optional asterisk before =)
        match = re.search(r'^([a-zA-Z_][a-zA-Z0-9_]*)\*?\s*=\s*\[([^\]]+)\]', line)
        if match:
            field_name = match.group(1)
            items_str = match.group(2)
            items = [item.strip() for item in items_str.split(',')]
            choice_fields_map[field_name] = items

    # Second pass: parse all fields with condition resolution
    field_counter = {'Text': 1, 'Integer': 1, 'Boolean': 1, 'Choice': 1,
                     'Credential': 1, 'Large Text': 1, 'Script': 1, 'Array': 1}

    for line in lines[2:]:
        fields = parse_field_line(line, field_counter, choice_fields_map)
        result['fields'].extend(fields)

    return result


def generate_extension_id(name: str, project_prefix: Optional[str] = None) -> str:
    """Generate extension ID from name with optional project prefix

    Args:
        name: Extension name
        project_prefix: Optional project prefix (e.g., 'cs' becomes 'ue-cs-name')
    """
    base_name = name.lower().replace(' ', '-').replace('_', '-')
    if project_prefix:
        return f'ue-{project_prefix}-{base_name}'
    return f'ue-{base_name}'


def generate_var_prefix(name: str, project_prefix: Optional[str] = None) -> str:
    """Generate variable prefix from name with optional project prefix

    Args:
        name: Extension name
        project_prefix: Optional project prefix (e.g., 'cs' becomes 'ue_cs_name')
    """
    base_name = name.lower().replace(' ', '_').replace('-', '_')
    if project_prefix:
        return f'ue_{project_prefix}_{base_name}'
    return f'ue_{base_name}'


def normalize_field_type(field_type: str) -> str:
    """Normalize field type with support for partial/abbreviated types

    Args:
        field_type: Raw field type string (e.g., 'C', 'Dyn', 'Int', 'Choice')

    Returns:
        Normalized full field type name

    Examples:
        'C' -> 'Credential'
        'D' or 'Dyn' -> 'Dynamic'
        'Ch' or 'Cho' -> 'Choice'
        'I' or 'Int' -> 'Integer'
    """
    # Normalize input: strip and capitalize first letter
    ft = field_type.strip()
    if not ft:
        return 'Text'  # Default fallback

    # Single letter shortcuts
    single_letter_map = {
        'C': 'Credential',
        'D': 'Dynamic',
        'B': 'Boolean',
        'I': 'Integer',
        'T': 'Text',
        'S': 'Script',
        'A': 'Array',
        'L': 'Large',
        'O': 'Output',
        'J': 'JSON',
        'Y': 'YAML',
    }

    if len(ft) == 1:
        upper = ft.upper()
        if upper in single_letter_map:
            return single_letter_map[upper]

    # Lowercase for matching
    ft_lower = ft.lower()

    # Full type names (exact matches)
    full_types = [
        'Text', 'Large Text', 'Integer', 'Float', 'Boolean', 'Choice',
        'Credential', 'Script', 'Array', 'Dynamic', 'Output', 'JSON',
        'YAML', 'Large', 'Sap Connection', 'Database Connection'
    ]

    # Check exact match (case-insensitive)
    for full_type in full_types:
        if ft_lower == full_type.lower():
            return full_type

    # Partial matching: find types that start with the input
    matches = []
    for full_type in full_types:
        if full_type.lower().startswith(ft_lower):
            matches.append(full_type)

    # Return first match, or default to Text
    if matches:
        return matches[0]

    return 'Text'  # Default fallback


def parse_field_line(line: str, field_counter: Dict, choice_fields_map: Dict) -> List[Dict[str, Any]]:
    """Parse a single field definition line"""

    # Check if there's an 'if' condition at the end
    condition = None
    if ' if ' in line:
        line_parts = line.rsplit(' if ', 1)
        line = line_parts[0]
        condition_part = line_parts[1].strip()
        condition = parse_condition(condition_part, choice_fields_map)

    # Check for comma-separated field names (grouped fields)
    if '(' in line and ')' in line:
        match = re.search(r'([^(]+)\(([^)]+)\)(\*)?', line)
        if match:
            fields_part = match.group(1).strip()
            type_in_parens = match.group(2)
            required_after_parens = match.group(3) == '*'

            # Check if it's comma-separated field names
            if ',' in fields_part:
                field_names = [name.strip().rstrip('*') for name in fields_part.split(',')]
                fields = []
                for field_name in field_names:
                    field_def = create_field_definition(
                        field_name,
                        type_in_parens,
                        required_after_parens,
                        None,
                        None,
                        False,
                        condition,
                        field_counter
                    )
                    fields.append(field_def)
                return fields

    # Parse single field
    field = parse_single_field(line, condition, field_counter, choice_fields_map)
    return [field] if field else []


def parse_single_field(line: str, condition: Optional[Dict],
                       field_counter: Dict, choice_fields_map: Dict) -> Optional[Dict[str, Any]]:
    """Parse a single field definition"""

    # Pattern 0/0.5/1: fieldname(Type) with optional * and optional = [...]
    # This handles: Dynamic with dependencies, Array with headers, or any other type
    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]+)\)(\*)?\s*(?:=\s*\[([^\]]+)\])?', line)
    if match:
        field_name = match.group(1)
        raw_field_type = match.group(2)
        required = match.group(3) == '*'
        list_content = match.group(4)  # Content inside [...] if present

        # Normalize the field type
        field_type = normalize_field_type(raw_field_type)

        # Handle special cases based on normalized type
        if field_type == 'Dynamic' and list_content:
            # Dynamic field with dependencies
            dependencies = [dep.strip() for dep in list_content.split(',')]
            return create_field_definition(
                field_name, 'Dynamic', required, None, None, False, condition, field_counter,
                dependencies=dependencies
            )
        elif field_type == 'Array' and list_content:
            # Array field with headers
            headers = [h.strip() for h in list_content.split(',')]
            return create_field_definition(
                field_name, 'Array', required, None, None, False, condition, field_counter,
                array_headers=headers
            )
        else:
            # Regular field type
            return create_field_definition(
                field_name, field_type, required, None, None, False, condition, field_counter
            )

    # Pattern 2: fieldname = [items] = default (choice with default) - CHECK THIS FIRST
    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\[([^\]]+)\]\s*=\s*(.+)', line)
    if match:
        field_name = match.group(1)
        items_str = match.group(2)
        default_value = match.group(3).strip()
        items = [item.strip() for item in items_str.split(',')]
        return create_field_definition(
            field_name, 'Choice', False, default_value, items, False, condition, field_counter
        )

    # Pattern 3: fieldname* = [items] (required choice - asterisk before equals)
    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\*\s*=\s*\[([^\]]+)\]', line)
    if match:
        field_name = match.group(1)
        items_str = match.group(2)
        items = [item.strip() for item in items_str.split(',')]
        return create_field_definition(
            field_name, 'Choice', True, None, items, False, condition, field_counter
        )

    # Pattern 4: fieldname = [items][] (multi-select)
    # Pattern 5: fieldname = [items]* (required choice)
    # Pattern 6: fieldname = [items] (choice)
    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\[([^\]]+)\](\[\])?(\*)?', line)
    if match:
        field_name = match.group(1)
        items_str = match.group(2)
        multi_select = match.group(3) == '[]'
        required = match.group(4) == '*'
        items = [item.strip() for item in items_str.split(',')]
        return create_field_definition(
            field_name, 'Choice', required, None, items, multi_select, condition, field_counter
        )

    # Pattern 6: fieldname* = value (required with default - non-choice)
    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\*\s*=\s*(.+)', line)
    if match:
        field_name = match.group(1)
        default_value = match.group(2).strip()
        field_type = infer_type_from_value(default_value)
        return create_field_definition(
            field_name, field_type, True, default_value, None, False, condition, field_counter
        )

    # Pattern 7: fieldname = value (with default)
    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)', line)
    if match:
        field_name = match.group(1)
        default_value = match.group(2).strip()
        field_type = infer_type_from_value(default_value)
        return create_field_definition(
            field_name, field_type, False, default_value, None, False, condition, field_counter
        )

    # Pattern 8: fieldname* (required text)
    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\*', line)
    if match:
        field_name = match.group(1)
        return create_field_definition(
            field_name, 'Text', True, None, None, False, condition, field_counter
        )

    # Pattern 9: fieldname (text)
    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)', line)
    if match:
        field_name = match.group(1)
        return create_field_definition(
            field_name, 'Text', False, None, None, False, condition, field_counter
        )

    raise ValueError(f"Unable to parse field definition: {line}")


def infer_type_from_value(value: str) -> str:
    """Infer field type from default value"""
    value = value.strip()

    if value.lower() in ('true', 'false'):
        return 'Boolean'

    try:
        int(value)
        return 'Integer'
    except ValueError:
        pass

    return 'Text'


def parse_condition(condition_str: str, choice_fields_map: Dict) -> Dict[str, Any]:
    """Parse the 'if' condition"""
    condition_str = condition_str.strip()

    # Handle negation: !field_name
    if condition_str.startswith('!'):
        field_name = condition_str[1:].strip()
        return {
            field_name: 'false'
        }

    # Handle comparison: field = value or field = 1,3
    if '=' in condition_str:
        parts = condition_str.split('=', 1)
        field_name = parts[0].strip()
        value_part = parts[1].strip()

        # Check if it's a comma-separated list (OR condition)
        if ',' in value_part:
            indices = [v.strip() for v in value_part.split(',')]
            # Resolve indices to actual values if it's a choice field
            if field_name in choice_fields_map:
                values = []
                for idx in indices:
                    try:
                        idx_num = int(idx) - 1  # Convert to 0-based
                        if 0 <= idx_num < len(choice_fields_map[field_name]):
                            values.append(choice_fields_map[field_name][idx_num])
                    except ValueError:
                        values.append(idx)
                # For multiple values, return as comma-separated string
                return {field_name: ','.join(values)}
            return {field_name: ','.join(indices)}
        else:
            # Single value
            value = value_part
            # Try to resolve index if it's a choice field
            if field_name in choice_fields_map:
                try:
                    idx = int(value) - 1  # Convert to 0-based
                    if 0 <= idx < len(choice_fields_map[field_name]):
                        value = choice_fields_map[field_name][idx]
                except ValueError:
                    pass

            return {field_name: value}

    # Handle simple boolean: field_name (means field = true)
    return {condition_str: 'true'}


def create_field_definition(
    field_name: str,
    field_type: str,
    required: bool,
    default: Optional[str],
    items: Optional[List[str]],
    multi_select: bool,
    condition: Optional[Dict],
    field_counter: Dict,
    dependencies: Optional[List[str]] = None,
    array_headers: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a field definition dictionary"""

    # Map special types
    actual_type = field_type
    extra_props = {}

    if field_type == 'Dynamic':
        actual_type = 'Choice'
        extra_props['dynamic'] = True
        extra_props['start'] = True
        items = []  # Dynamic fields start with empty items
        if dependencies:
            extra_props['dependencies'] = dependencies
    elif field_type == 'Credential':
        # Credential fields have special properties
        extra_props['start'] = True
        extra_props['span'] = 2
        extra_props['allow_variable'] = True
    elif field_type == 'Output':
        actual_type = 'Text'
        extra_props['restriction'] = 'Output Only'
        extra_props['raw'] = {'preserveOutputOnRerun': True}
    elif field_type == 'JSON':
        actual_type = 'Large Text'
        extra_props['text_type'] = 'JSON'
    elif field_type == 'YAML':
        actual_type = 'Large Text'
        extra_props['text_type'] = 'YAML'
    elif field_type == 'Large':
        actual_type = 'Large Text'
    elif field_type == 'Array':
        # Array fields with headers
        if array_headers and len(array_headers) >= 2:
            extra_props['name_title'] = array_headers[0]
            extra_props['value_title'] = array_headers[1]

    field_def = {
        field_name: actual_type
    }

    # Add hint (can be filled in later)
    field_def['hint'] = f'The {field_name_to_label(field_name)}'

    # Add field mapping
    field_def['field_mapping'] = generate_field_mapping(actual_type, field_counter)

    if default is not None:
        field_def['default'] = default

    if items is not None:
        # Store items as simple strings
        # For Dynamic fields, items will be an empty list
        field_def['items'] = items

    if multi_select:
        field_def['allow_multiple'] = True
        field_def['allow_empty'] = True

    # Handle required and show_if together
    if condition:
        field_def['show_if'] = condition
        # If field is required AND has a condition, put required inside show_if
        if required:
            field_def['show_if']['required'] = True
    else:
        # If field is required but has NO condition, put required at top level
        if required:
            field_def['required'] = True

    # Add extra properties
    field_def.update(extra_props)

    # Add allow_variable default (only if not already set by extra_props)
    if 'allow_variable' not in field_def:
        field_def['allow_variable'] = None

    # Add start/end markers (simplified - first field starts, last ends)
    # This would need more sophisticated logic in a real implementation

    return field_def


def field_name_to_label(field_name: str) -> str:
    """Convert field_name to a human-readable label"""
    words = field_name.split('_')
    return ' '.join(word.capitalize() for word in words)


def generate_field_mapping(field_type: str, field_counter: Dict) -> str:
    """Generate field mapping based on type"""
    type_mapping = {
        'Text': 'Text Field',
        'Integer': 'Integer Field',
        'Boolean': 'Boolean Field',
        'Choice': 'Choice Field',
        'Credential': 'Credential Field',
        'Large Text': 'Large Text Field',
        'Script': 'Script Field',
        'Array': 'Array Field',
    }

    base_mapping = type_mapping.get(field_type, 'Text Field')
    counter = field_counter.get(field_type, 1)
    field_counter[field_type] = counter + 1

    return f"{base_mapping} {counter}"
