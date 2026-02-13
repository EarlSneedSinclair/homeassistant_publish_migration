#!/usr/bin/env python3
"""
Optolink Splitter - Home Assistant Auto Discovery Migration Script: 
homeassistant_create_entities.json -> homeassistant_publish.py

Converts:
- homeassistant_entities.json + poll_list.py -> homeassistant_poll_list.py

This script combines the separate entity configuration and poll list
into the unified structure for the current homeassistant_publish approach.

Usage:
    python migrate_ha_entities_to_ha_publish.py                           # Interactive mode with defaults
    python migrate_ha_entities_to_ha_publish.py homeassistant_entities.json poll_list.py
    python migrate_ha_entities_to_ha_publish.py homeassistant_entities.json poll_list.py -o output.py
"""

import json
import re
import sys
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Set


def parse_poll_list_file(filepath: str) -> List[Tuple]:
    """Parse poll_list.py and extract poll_items list."""
    # Try multiple encodings (Windows and Unix)
    encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1', 'iso-8859-1']
    content = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding, errors='strict') as f:
                content = f.read()
            used_encoding = encoding
            break
        except (UnicodeDecodeError, LookupError):
            continue
    
    if content is None:
        raise ValueError(f"Could not read file with any encoding: {encodings}")
    
    print(f"[OK] Successfully read poll_list file with {used_encoding} encoding")
    
    namespace = {}
    try:
        exec(content, namespace)
    except Exception as e:
        print(f"[ERROR] Error executing poll_list file: {e}")
        raise
    
    if 'poll_items' not in namespace:
        raise ValueError("poll_items not found in file")
    
    return namespace['poll_items']


def load_entities_json(filepath: str) -> Dict:
    """Load entities JSON with multiple encoding support."""
    encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1', 'iso-8859-1']
    used_encoding = None
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding, errors='strict') as f:
                data = json.load(f)
            used_encoding = encoding
            break
        except (UnicodeDecodeError, json.JSONDecodeError, LookupError):
            continue
    
    if used_encoding is None:
        raise ValueError(f"Could not read JSON file with any encoding: {encodings}")
    
    print(f"[OK] Successfully read JSON file with {used_encoding} encoding")
    return data


def normalize_name(name: str) -> str:
    """Convert name to lowercase and replace non-alphanumeric with underscore."""
    return re.sub(r'[^0-9a-zA-Z]+', '_', name).lower().strip('_')


def normalize_for_matching(name: str) -> str:
    """Normalize name for matching - removes all non-alphanumeric."""
    return re.sub(r'[^0-9a-z]+', '', name.lower())


def parse_poll_item(item: Tuple) -> Dict[str, Any]:
    """
    Parse a poll item tuple.
    Format: ([PollCycle,] Name, DpAddr, Length [, Scale/Type [, Signed]])
    """
    result = {}
    idx = 0
    
    # Check if first element is PollCycle
    if isinstance(item[0], int) and len(item) > 3 and isinstance(item[1], str):
        result['pollcycle'] = item[0]
        idx = 1
    else:
        result['pollcycle'] = 1
        idx = 0
    
    result['name'] = item[idx]
    result['dpaddr'] = item[idx + 1]
    result['length'] = item[idx + 2]
    
    if idx + 3 < len(item):
        result['scale'] = item[idx + 3]
    if idx + 4 < len(item):
        result['signed'] = item[idx + 4]
    
    return result


def create_poll_tuple(poll_data: Dict) -> Tuple:
    """Create a poll tuple from poll data, preserving original types."""
    parts = [
        poll_data.get('pollcycle', 1),
        poll_data['name'],
        poll_data['dpaddr'],
        poll_data['length']
    ]
    
    if 'scale' in poll_data:
        parts.append(poll_data['scale'])
    if 'signed' in poll_data:
        parts.append(poll_data['signed'])
    
    return tuple(parts)


def transform_command_template(template: str, dpaddr: Any, length: int) -> str:
    """
    Transform command_template to use placeholders.
    
    Examples:
        '{{ "w;0x3007;2;"~value*10 }}' -> '{{ "w;%DpAddr%;%Length%;"~value*10 }}'
    """
    if not template or '%DpAddr%' in template:
        return template
    
    # Convert dpaddr to hex string
    if isinstance(dpaddr, int):
        dpaddr_str = f"0x{dpaddr:04X}"
    else:
        dpaddr_str = str(dpaddr)
    
    # Replace the address and length in the template
    template = template.replace(dpaddr_str.lower(), '%DpAddr%')
    template = template.replace(dpaddr_str.upper(), '%DpAddr%')
    template = template.replace(dpaddr_str, '%DpAddr%')
    template = template.replace(f';{length};', ';%Length%;')
    
    return template


def group_entities_by_domain(entities: List[Dict], poll_items_map: Dict[str, Dict]) -> Dict:
    """Group entities by domain and similar attributes."""
    domains = defaultdict(lambda: {'base_attrs': {}, 'units': defaultdict(list)})
    
    for entity in entities:
        domain = entity.get('domain', 'sensor')
        name_normalized = normalize_name(entity.get('name', ''))
        name_for_matching = normalize_for_matching(entity.get('name', ''))
        
        poll_data = poll_items_map.get(name_for_matching)
        
        entity_attrs = {}
        for key, value in entity.items():
            if key in ['name', 'domain']:
                continue
            
            # Transform command_topic
            if key == 'command_topic' and value == 'cmnd':
                entity_attrs[key] = '%mqtt_listen%'
            # Transform command_template to use placeholders
            elif key == 'command_template' and poll_data:
                entity_attrs[key] = transform_command_template(
                    value, poll_data['dpaddr'], poll_data['length']
                )
            else:
                entity_attrs[key] = value
        
        # Create grouping key
        group_key = (
            entity_attrs.get('device_class'),
            entity_attrs.get('entity_category'),
            entity_attrs.get('payload_off'),
            entity_attrs.get('payload_on'),
            entity_attrs.get('icon') if domain in ['binary_sensor', 'sensor'] else None
        )
        
        if poll_data:
            poll_tuple = create_poll_tuple(poll_data)
            domains[domain]['units'][group_key].append({
                'poll_tuple': poll_tuple,
                'attrs': entity_attrs,
                'original_name': entity.get('name', '')
            })
        else:
            nopoll_tuple = (0, name_normalized, 0x0000, 1, 1, False)
            domains[domain]['units'][group_key].append({
                'nopoll_tuple': nopoll_tuple,
                'attrs': entity_attrs,
                'original_name': entity.get('name', '')
            })
    
    return domains


def build_poll_list_structure(entities_json: Dict, poll_items_map: Dict[str, Dict]) -> Tuple[Dict, Dict]:
    """Build the complete poll_list structure and return coverage info."""
    result = {
        'device': entities_json.get('device', {}),
        'node_id': entities_json.get('mqtt_ha_node_id', '').rstrip('/'),
        'dp_prefix': entities_json.get('dp_prefix', ''),
        'discovery_prefix': entities_json.get('mqtt_ha_discovery_prefix', 'homeassistant'),
        'beautifier': {
            'search': ['ae', 'oe', 'ue'],
            'replace': ['ä', 'ö', 'ü'],
            'fixed': ['VD', 'HK2', 'KK', 'PK', 'SK', 'SCOP']
        },
        'poll_interval': 1,
        'mqtt_delay': 0.1,
    }
    
    grouped = group_entities_by_domain(entities_json['datapoints'], poll_items_map)
    
    # Track which poll items were used
    used_poll_items = set()
    entity_names = set()
    
    # Attributes that should NOT be promoted to domain level
    entity_specific_attrs = {
        'state_topic', 'current_temperature_topic',
        'temperature_state_topic', 'mode_state_topic', 
        'preset_mode_state_topic', 'value_template',
        'max', 'min', 'step', 'mode'
    }
    
    domains = []
    for domain, domain_data in grouped.items():
        domain_config = {'domain': domain}
        units_data = domain_data['units']
        
        # Check if this is a complex domain (climate, water_heater)
        is_complex_domain = domain in ['climate', 'water_heater']
        
        if len(units_data) == 1:
            # Single group
            group_key, entities = list(units_data.items())[0]
            
            # Track entity names
            for ent in entities:
                entity_names.add(ent['original_name'])
                if 'poll_tuple' in ent:
                    used_poll_items.add(normalize_for_matching(ent['poll_tuple'][1]))
            
            # Check if single entity without poll data
            if len(entities) == 1 and 'nopoll_tuple' in entities[0]:
                entity = entities[0]
                domain_config['entity_name'] = entity['nopoll_tuple'][1]
                for key, value in entity['attrs'].items():
                    domain_config[key] = value
                
                # Add warning for complex domains
                if is_complex_domain:
                    domain_config['_WARNING'] = (
                        'This is a complex domain. Manual review recommended. '
                        'Templates may need adjustment.'
                    )
            else:
                # Multiple entities or has poll data
                if entities:
                    first_entity = entities[0]['attrs']
                    for key, value in first_entity.items():
                        if key in entity_specific_attrs:
                            continue
                        if all(e['attrs'].get(key) == value for e in entities):
                            domain_config[key] = value
                
                poll_list = [ent['poll_tuple'] for ent in entities if 'poll_tuple' in ent]
                nopoll_list = [ent['nopoll_tuple'] for ent in entities if 'nopoll_tuple' in ent]
                
                if poll_list:
                    domain_config['poll'] = poll_list
                if nopoll_list:
                    domain_config['nopoll'] = nopoll_list
            
            domains.append(domain_config)
        
        else:
            # Multiple groups - use units structure
            units = []
            for group_key, entities in units_data.items():
                unit_config = {}
                
                # Track entity names
                for ent in entities:
                    entity_names.add(ent['original_name'])
                    if 'poll_tuple' in ent:
                        used_poll_items.add(normalize_for_matching(ent['poll_tuple'][1]))
                
                # Check if single entity without poll data
                if len(entities) == 1 and 'nopoll_tuple' in entities[0]:
                    entity = entities[0]
                    unit_config['entity_name'] = entity['nopoll_tuple'][1]
                    for key, value in entity['attrs'].items():
                        unit_config[key] = value
                else:
                    # Multiple entities or has poll data
                    if entities:
                        first_entity = entities[0]['attrs']
                        for key, value in first_entity.items():
                            if key in entity_specific_attrs:
                                continue
                            if all(e['attrs'].get(key) == value for e in entities):
                                unit_config[key] = value
                    
                    poll_list = [ent['poll_tuple'] for ent in entities if 'poll_tuple' in ent]
                    nopoll_list = [ent['nopoll_tuple'] for ent in entities if 'nopoll_tuple' in ent]
                    
                    if poll_list:
                        unit_config['poll'] = poll_list
                    if nopoll_list:
                        unit_config['nopoll'] = nopoll_list
                
                units.append(unit_config)
            
            domain_config['units'] = units
            domains.append(domain_config)
    
    result['domains'] = domains
    
    # Build coverage report
    coverage = {
        'used_poll_items': used_poll_items,
        'all_poll_items': set(poll_items_map.keys()),
        'entity_names': entity_names,
        'total_entities': len(entities_json.get('datapoints', []))
    }
    
    return result, coverage


def format_tuple(t: Tuple, indent: int = 0) -> str:
    """Format a tuple with proper representation of values."""
    parts = []
    for i, item in enumerate(t):
        if isinstance(item, bool):
            parts.append('True' if item else 'False')
        elif isinstance(item, int):
            # First element (PollCycle) is always decimal
            # Third element (DpAddr) is hex if >= 256
            # Fourth element (Length) is always decimal
            if i == 0:  # PollCycle
                parts.append(str(item))
            elif i == 2:  # DpAddr
                if item >= 256:
                    parts.append(f"0x{item:04X}")
                else:
                    parts.append(str(item))
            elif i == 3:  # Length
                parts.append(str(item))
            else:
                parts.append(str(item))
        elif isinstance(item, float):
            parts.append(repr(item))
        elif isinstance(item, str):
            # Use double quotes for strings
            parts.append(f'"{item}"')
        else:
            parts.append(repr(item))
    
    return f"({', '.join(parts)})"


def format_string(s: str) -> str:
    """Format string with double quotes and proper escaping."""
    # Escape backslashes and double quotes
    s = s.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{s}"'


def write_dict(f, d: Dict, indent: int = 0, comment_out: bool = False):
    """Write a dict with proper formatting."""
    ind = '    ' * indent
    prefix = '# ' if comment_out else ''
    
    # Check for warning
    warning = d.pop('_WARNING', None)
    
    f.write('{\n')
    
    if warning:
        f.write(f'{prefix}{ind}    # WARNING: {warning}\n')
    
    items = list(d.items())
    for i, (key, value) in enumerate(items):
        comma = ',' if i < len(items) - 1 else ''
        f.write(f'{prefix}{ind}    "{key}": ')
        
        if isinstance(value, dict):
            write_dict(f, value, indent + 1, comment_out)
        elif isinstance(value, list):
            write_list(f, value, indent + 1, comment_out)
        elif isinstance(value, str):
            f.write(format_string(value))
        elif isinstance(value, bool):
            f.write('True' if value else 'False')
        elif isinstance(value, (int, float)):
            f.write(str(value))
        elif value is None:
            f.write('None')
        else:
            f.write(repr(value))
        
        f.write(comma + '\n')
    
    f.write(f'{prefix}{ind}}}')


def write_list(f, lst: List, indent: int = 0, comment_out: bool = False):
    """Write a list with proper formatting."""
    if not lst:
        f.write('[]')
        return
    
    ind = '    ' * indent
    prefix = '# ' if comment_out else ''
    
    # Check if list of tuples (poll items)
    if isinstance(lst[0], tuple):
        f.write('[\n')
        for item in lst:
            formatted = format_tuple(item)
            f.write(f'{prefix}{ind}    {formatted},\n')
        f.write(f'{prefix}{ind}]')
    
    # Check if list of dicts (units)
    elif isinstance(lst[0], dict):
        f.write('[\n')
        for item in lst:
            f.write(f'{prefix}{ind}    ')
            write_dict(f, item, indent + 1, comment_out)
            f.write(',\n')
        f.write(f'{prefix}{ind}]')
    
    # Simple list
    else:
        f.write('[')
        for i, item in enumerate(lst):
            if isinstance(item, str):
                f.write(format_string(item))
            else:
                f.write(repr(item))
            if i < len(lst) - 1:
                f.write(', ')
        f.write(']')


def write_poll_list_file(poll_list: Dict, output_path: str, coverage: Dict):
    """Write the poll_list structure to a Python file with UTF-8 encoding."""
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        # Header
        f.write("""'''
   Copyright 2026 matthias-oe

   Licensed under the GNU GENERAL PUBLIC LICENSE, Version 3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       https://www.gnu.org/licenses/gpl-3.0.html

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

   This file was automatically generated by migrate_ha_entities_to_ha_publish.py
   
   IMPORTANT - Manual Review Required:
   The migration has created a foundation and migrated as much as possible,
   but manual adjustments are needed for a working result - especially for
   templates and complex domains.
   
   This script provides an alternative definition for Optolink-Splitter datapoints,
   enhanced with MQTT publishing attributes for Home Assistant entities.
   
   The 'poll_list' is processed in the homeassistant_adapter with the appropriate
   conversion for its use in the Optolink Splitter. Additionally, the 'poll_list'
   will be utilized in homeassistant_publish.py to publish Home Assistant entities
   via MQTT.
'''\n\n""")
        
        # Write coverage report as comments
        if coverage:
            unused = coverage['all_poll_items'] - coverage['used_poll_items']
            if unused:
                f.write("# ======================================================================\n")
                f.write("# This report was automatically generated by migrate_ha_entities_to_ha_publish.py\n")
                f.write("# ======================================================================\n")
                f.write("#\n")
                f.write("# MIGRATION REPORT:\n")
                f.write(f"# - Total entities processed: {coverage['total_entities']}\n")
                f.write(f"# - Poll items used: {len(coverage['used_poll_items'])}\n")
                f.write(f"# - Poll items NOT used: {len(unused)}\n")
                f.write("#\n# Unused poll items (may need manual review):\n")
                for item in sorted(unused):
                    f.write(f"#   - {item}\n")
                f.write("\n")
        
        f.write("poll_list = {\n")
        
        # Write top-level keys
        for key in ['device', 'node_id', 'dp_prefix', 'discovery_prefix', 'beautifier', 
                    'poll_interval', 'mqtt_delay']:
            if key in poll_list:
                f.write(f'    "{key}": ')
                value = poll_list[key]
                
                if isinstance(value, dict):
                    write_dict(f, value, 1)
                elif isinstance(value, list):
                    write_list(f, value, 1)
                elif isinstance(value, str):
                    f.write(repr(value))
                elif isinstance(value, (int, float)):
                    f.write(str(value))
                else:
                    f.write(repr(value))
                
                f.write(',\n')
        
        # Write domains
        f.write('    "domains": [\n')
        
        for domain in poll_list.get('domains', []):
            # Check if this should be commented out
            comment_out = domain.get('domain') in ['climate', 'water_heater'] and 'entity_name' in domain
            
            if comment_out:
                f.write('\n# ' + ' '*8 + 'NOTE: Complex domain - please review and uncomment after verification\n')
                f.write('# ' + ' '*8)
            else:
                f.write('        ')
            
            write_dict(f, domain, 2, comment_out)
            f.write(',\n')
        
        f.write('    ]\n')
        f.write('}\n')


def print_usage():
    """Print detailed usage information."""
    print("""
+======================================================================+
|  Optolink Splitter - Home Assistant Auto Discovery Migration        |
|  homeassistant_create_entities.json -> homeassistant_publish.py     |
+======================================================================+

This script migrates from the old entity structure to the new poll_list
format for Home Assistant integration with Optolink-Splitter.

USAGE:
    python migrate_ha_entities_to_ha_publish.py                           # Use defaults
    python migrate_ha_entities_to_ha_publish.py <entities_json> <poll_list>
    python migrate_ha_entities_to_ha_publish.py <entities_json> <poll_list> -o <output>

REQUIRED INPUT FILES:

  1. entities JSON file (default: homeassistant_entities.json)
     Contains entity definitions with attributes like:
     - name, domain, device_class, icon
     - unit_of_measurement, state_class
     - command_topic, command_template
     Example location: ./homeassistant_entities.json

  2. poll_list Python file (default: poll_list.py)
     Contains poll items as Python tuples:
     poll_items = [
         (PollCycle, Name, DpAddr, Length, Scale, Signed),
         ...
     ]
     Example location: ./poll_list.py

OUTPUT:
     homeassistant_poll_list.py (or specified with -o)
     Combined structure with poll items and entity attributes

EXAMPLES:
     # Use default filenames (homeassistant_entities.json and poll_list.py)
     python migrate_ha_entities_to_ha_publish.py

     # Specify input files
     python migrate_ha_entities_to_ha_publish.py homeassistant_entities.json poll_list.py

     # Specify output file
     python migrate_ha_entities_to_ha_publish.py homeassistant_entities.json poll_list.py -o output.py

WHAT GETS MIGRATED:
     - Entity definitions combined with poll items
     - Templates converted to use placeholders (%DpAddr%, %Length%)
     - Command topics converted to %mqtt_listen%
     - Grouping by domain and attributes
     - UTF-8 characters (°C, ä, ö, ü) preserved

AFTER MIGRATION:
     1. Review climate and water_heater domains (marked as commented out)
     2. Check template placeholders
     3. Verify all entities are included
     4. Adjust beautifier settings if needed
""")


def migrate(entities_json_path: str, poll_list_path: str, output_path: str):
    """Main migration function."""
    print("\n" + "="*70)
    print("Optolink Splitter - Home Assistant Auto Discovery Migration")
    print("="*70)
    
    print(f"\nLoading {entities_json_path}...")
    entities_json = load_entities_json(entities_json_path)
    
    print(f"Loading {poll_list_path}...")
    poll_items = parse_poll_list_file(poll_list_path)
    
    print(f"\n[OK] Found {len(poll_items)} poll items")
    print(f"[OK] Found {len(entities_json.get('datapoints', []))} entities")
    
    # Create map of poll items
    poll_items_map = {}
    for item in poll_items:
        parsed = parse_poll_item(item)
        name_for_matching = normalize_for_matching(parsed['name'])
        poll_items_map[name_for_matching] = parsed
    
    print("\nBuilding poll_list structure...")
    poll_list, coverage = build_poll_list_structure(entities_json, poll_items_map)
    
    print(f"Writing output to {output_path}...")
    write_poll_list_file(poll_list, output_path, coverage)
    
    print("\n" + "="*70)
    print("[OK] Migration complete!")
    print("="*70)
    
    # Print coverage report
    unused = coverage['all_poll_items'] - coverage['used_poll_items']
    print(f"\n[Coverage Report]")
    print(f"  - Entities processed: {coverage['total_entities']}")
    print(f"  - Poll items used: {len(coverage['used_poll_items'])}/{len(coverage['all_poll_items'])}")
    
    if unused:
        print(f"\n[WARNING] {len(unused)} poll items were NOT used:")
        for item in sorted(unused):
            # Find original name from poll_items_map
            original = poll_items_map[item]['name']
            print(f"     - {original}")
        print("\n  -> These items exist in poll_list but have no matching entity")
        print("  -> May be intentional or may need manual review")
    
    print(f"\nGenerated file: {output_path}")
    print("\n" + "="*70)
    print("IMPORTANT - Manual Review Required:")
    print("="*70)
    print("The migration has created a foundation and migrated as much as")
    print("possible, but manual adjustments are needed for a working result:")
    print("")
    print("  - Climate/water_heater domains are COMMENTED OUT")
    print("    -> Review templates and uncomment after verification")
    print("  - Verify template placeholders (%DpAddr%, %Length%, %mqtt_listen%)")
    print("  - Check entity groupings and adjust if needed")
    print("  - Adjust beautifier settings if needed")
    print("="*70)
    print()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migrate from old entity structure to new poll_list format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )
    
    parser.add_argument('entities_json', nargs='?', default='homeassistant_entities.json',
                        help='Path to entities JSON file (default: homeassistant_entities.json)')
    parser.add_argument('poll_list', nargs='?', default='poll_list.py',
                        help='Path to poll_list.py (default: poll_list.py)')
    parser.add_argument('-o', '--output', default='homeassistant_poll_list.py',
                        help='Output path (default: homeassistant_poll_list.py)')
    parser.add_argument('-h', '--help', action='store_true',
                        help='Show detailed help message')
    
    args = parser.parse_args()
    
    if args.help:
        print_usage()
        sys.exit(0)
    
    # Check if default files exist
    import os
    if args.entities_json == 'homeassistant_entities.json' and not os.path.exists('homeassistant_entities.json'):
        print("\n" + "="*70)
        print("ERROR: Default file 'homeassistant_entities.json' not found!")
        print("="*70)
        print("\nPlease either:")
        print("  1. Place 'homeassistant_entities.json' in the current directory, OR")
        print("  2. Specify the file path:")
        print("     python migrate_ha_entities_to_ha_publish.py <path/to/entities.json> poll_list.py")
        print("\nFor full help: python migrate_ha_entities_to_ha_publish.py --help")
        sys.exit(1)
    
    if args.poll_list == 'poll_list.py' and not os.path.exists('poll_list.py'):
        print("\n" + "="*70)
        print("ERROR: Default file 'poll_list.py' not found!")
        print("="*70)
        print("\nPlease either:")
        print("  1. Place 'poll_list.py' in the current directory, OR")
        print("  2. Specify the file path:")
        print("     python migrate_ha_entities_to_ha_publish.py homeassistant_entities.json <path/to/poll_list.py>")
        print("\nFor full help: python migrate_ha_entities_to_ha_publish.py --help")
        sys.exit(1)
    
    try:
        migrate(args.entities_json, args.poll_list, args.output)
    except Exception as e:
        print(f"\n[ERROR] Error during migration: {e}")
        print("\nFor help, run: python migrate_ha_entities_to_ha_publish.py --help")
        sys.exit(1)
