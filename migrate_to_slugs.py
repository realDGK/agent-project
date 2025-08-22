#!/usr/bin/env python3
"""
Migration script to convert document type directories from number-based to slug-based naming.
Creates a mapping file and renames all directories.
"""

import os
import re
import json
import shutil
from pathlib import Path
from typing import Dict, Tuple

def create_slug(name: str) -> str:
    """
    Convert a directory name to a clean slug format.
    Examples:
        "1.Articles_of_incorporation" -> "articles-of-incorporation"
        "26_Purchase_Sale_Agreement_(PSA)" -> "purchase-sale-agreement-psa"
        "3: Operating Agreement" -> "operating-agreement"
    """
    # Remove leading numbers and separators (handles: "1.", "26_", "3:", etc.)
    name = re.sub(r'^\d+[._:\-\s]+', '', name)
    
    # Convert parentheses content to be part of the slug
    name = name.replace('(', ' ').replace(')', ' ')
    
    # Replace special characters and spaces with hyphens
    name = re.sub(r'[_\s]+', '-', name)
    name = re.sub(r'[^a-zA-Z0-9\-]', '', name)
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove multiple consecutive hyphens
    name = re.sub(r'-+', '-', name)
    
    # Remove leading/trailing hyphens
    name = name.strip('-')
    
    return name

def analyze_directories(base_path: Path) -> Dict[str, str]:
    """
    Analyze all directories and generate slug mappings.
    Returns dict of {old_name: new_slug}
    """
    mappings = {}
    
    for dir_path in sorted(base_path.iterdir()):
        if dir_path.is_dir():
            old_name = dir_path.name
            
            # Skip directories that are already processed or special
            if old_name.startswith('.') or old_name in ['batchfile', 'checklist.txt']:
                continue
                
            new_slug = create_slug(old_name)
            
            # Ensure uniqueness
            if new_slug in mappings.values():
                # Find the original number if it exists
                match = re.match(r'^(\d+)', old_name)
                if match:
                    new_slug = f"{new_slug}-{match.group(1)}"
                else:
                    counter = 2
                    base_slug = new_slug
                    while new_slug in mappings.values():
                        new_slug = f"{base_slug}-{counter}"
                        counter += 1
            
            if new_slug:  # Only add if we got a valid slug
                mappings[old_name] = new_slug
    
    return mappings

def validate_mappings(mappings: Dict[str, str]) -> Tuple[bool, list]:
    """
    Validate that all slugs are unique and valid.
    Returns (is_valid, list_of_issues)
    """
    issues = []
    slugs = list(mappings.values())
    
    # Check for duplicates
    seen = set()
    for slug in slugs:
        if slug in seen:
            issues.append(f"Duplicate slug: {slug}")
        seen.add(slug)
    
    # Check for empty slugs
    for old_name, slug in mappings.items():
        if not slug:
            issues.append(f"Empty slug for: {old_name}")
        if len(slug) < 3:
            issues.append(f"Slug too short for {old_name}: {slug}")
    
    return len(issues) == 0, issues

def perform_migration(base_path: Path, mappings: Dict[str, str], dry_run: bool = True) -> Dict:
    """
    Perform the actual directory renaming.
    If dry_run=True, only simulate and report what would happen.
    """
    results = {
        'renamed': [],
        'skipped': [],
        'errors': []
    }
    
    for old_name, new_slug in mappings.items():
        old_path = base_path / old_name
        new_path = base_path / new_slug
        
        if not old_path.exists():
            results['errors'].append(f"Source doesn't exist: {old_name}")
            continue
            
        if new_path.exists():
            results['skipped'].append(f"Target already exists: {new_slug}")
            continue
        
        if dry_run:
            results['renamed'].append(f"{old_name} -> {new_slug}")
        else:
            try:
                old_path.rename(new_path)
                results['renamed'].append(f"{old_name} -> {new_slug}")
            except Exception as e:
                results['errors'].append(f"Failed to rename {old_name}: {e}")
    
    return results

def save_mapping_file(mappings: Dict[str, str], output_path: Path):
    """Save the mapping to a JSON file for reference."""
    mapping_data = {
        'description': 'Mapping from old document type directory names to new slug-based names',
        'generated': str(Path.cwd()),
        'total_directories': len(mappings),
        'mappings': mappings,
        'reverse_mappings': {v: k for k, v in mappings.items()}
    }
    
    with open(output_path, 'w') as f:
        json.dump(mapping_data, f, indent=2)

def main():
    """Main migration function."""
    base_path = Path("/home/scott/agent-project/config/prompts/document_types")
    mapping_file = Path("/home/scott/agent-project/directory_name_mapping.json")
    
    print("=" * 60)
    print("Document Type Directory Migration to Slug Format")
    print("=" * 60)
    print(f"\nBase path: {base_path}")
    
    # Step 1: Analyze directories
    print("\n1. Analyzing directories...")
    mappings = analyze_directories(base_path)
    print(f"   Found {len(mappings)} directories to process")
    
    # Step 2: Validate mappings
    print("\n2. Validating slug mappings...")
    is_valid, issues = validate_mappings(mappings)
    if not is_valid:
        print("   ❌ Validation failed:")
        for issue in issues:
            print(f"      - {issue}")
        return 1
    print("   ✅ All slugs are valid and unique")
    
    # Step 3: Show preview
    print("\n3. Preview of changes (first 20):")
    for i, (old, new) in enumerate(list(mappings.items())[:20]):
        print(f"   {old:50} -> {new}")
        if i == 19 and len(mappings) > 20:
            print(f"   ... and {len(mappings) - 20} more")
    
    # Step 4: Dry run
    print("\n4. Performing dry run...")
    dry_results = perform_migration(base_path, mappings, dry_run=True)
    print(f"   Would rename: {len(dry_results['renamed'])} directories")
    print(f"   Would skip: {len(dry_results['skipped'])} directories")
    print(f"   Errors found: {len(dry_results['errors'])} issues")
    
    if dry_results['errors']:
        print("\n   Errors detected:")
        for error in dry_results['errors']:
            print(f"      - {error}")
        return 1
    
    # Step 5: Save mapping file
    print("\n5. Saving mapping file...")
    save_mapping_file(mappings, mapping_file)
    print(f"   Saved to: {mapping_file}")
    
    # Step 6: Ask for confirmation
    print("\n" + "=" * 60)
    print("Ready to perform actual migration!")
    print(f"This will rename {len(mappings)} directories.")
    response = input("Proceed? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("Migration cancelled.")
        return 0
    
    # Step 7: Perform actual migration
    print("\n6. Performing actual migration...")
    results = perform_migration(base_path, mappings, dry_run=False)
    
    print(f"\n✅ Migration complete!")
    print(f"   Renamed: {len(results['renamed'])} directories")
    if results['skipped']:
        print(f"   Skipped: {len(results['skipped'])} directories")
    if results['errors']:
        print(f"   Errors: {len(results['errors'])} issues")
        for error in results['errors']:
            print(f"      - {error}")
    
    print(f"\nMapping file saved at: {mapping_file}")
    print("You can use this file to reference the old->new name mappings if needed.")
    
    return 0

if __name__ == "__main__":
    exit(main())