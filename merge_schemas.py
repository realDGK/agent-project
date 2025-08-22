#!/usr/bin/env python3
"""
Script to merge all schema_additions.json files into the master schema.json
"""

import json
import os
from pathlib import Path
import glob

def load_json_file(filepath):
    """Load and parse a JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(filepath, data):
    """Save data to a JSON file with proper formatting"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')  # Add trailing newline

def merge_schema_additions():
    """Main function to merge all schema additions into master schema"""
    
    # Define paths
    master_schema_path = "/home/scott/agent-project/config/schema.json"
    document_types_dir = "/home/scott/agent-project/config/prompts/document_types"
    
    print("Loading master schema...")
    master_schema = load_json_file(master_schema_path)
    
    # Get the properties object where we'll add new fields
    # Check if it's array-based (items.properties) or object-based (properties)
    if 'items' in master_schema and 'properties' in master_schema['items']:
        target_properties = master_schema['items']['properties']
    elif 'properties' in master_schema:
        target_properties = master_schema['properties']
    else:
        print("Error: Master schema doesn't have expected structure (items.properties or properties)")
        return False
    
    # Find all schema_additions.json files (including with numeric prefixes like 163_schema_additions.json)
    schema_additions_pattern = os.path.join(document_types_dir, "**/*schema_additions.json")
    schema_files = glob.glob(schema_additions_pattern, recursive=True)
    
    print(f"Found {len(schema_files)} schema addition files")
    
    # Track what we're adding
    added_properties = []
    
    # Process each schema additions file
    for schema_file in sorted(schema_files):
        try:
            # Get directory name for context
            dir_name = os.path.basename(os.path.dirname(schema_file))
            print(f"Processing: {dir_name}/schema_additions.json")
            
            # Load the schema additions
            additions = load_json_file(schema_file)
            
            # Merge each property from the additions
            for prop_name, prop_definition in additions.items():
                if prop_name in target_properties:
                    print(f"  Warning: Property '{prop_name}' already exists in master schema, skipping...")
                else:
                    target_properties[prop_name] = prop_definition
                    added_properties.append(prop_name)
                    print(f"  Added: {prop_name}")
                    
        except json.JSONDecodeError as e:
            print(f"  Error: Failed to parse JSON in {schema_file}: {e}")
            continue
        except Exception as e:
            print(f"  Error processing {schema_file}: {e}")
            continue
    
    # Save the updated master schema
    print(f"\nSaving updated master schema with {len(added_properties)} new properties...")
    save_json_file(master_schema_path, master_schema)
    
    print(f"Successfully merged {len(added_properties)} new properties into master schema")
    print(f"New properties added: {', '.join(sorted(added_properties))}")
    
    return True

if __name__ == "__main__":
    success = merge_schema_additions()
    exit(0 if success else 1)