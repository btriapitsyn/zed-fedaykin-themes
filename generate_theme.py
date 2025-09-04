#!/usr/bin/env python3
"""
Zed Theme Generator for Fedaykin Themes

This script generates Zed themes from color palette files.
It manages multiple themes in a single themes/fedaykin-themes.json file.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

def load_palette(palette_path: str) -> Dict[str, Any]:
    """Load color palette from JSON file (with comment support)."""
    with open(palette_path, 'r') as f:
        content = f.read()

    # Remove single-line comments
    lines = []
    for line in content.split('\n'):
        # Find comment position, but ignore // inside strings
        comment_pos = -1
        in_string = False
        escape_next = False

        for i, char in enumerate(line):
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
            if not in_string and line[i:i+2] == '//':
                comment_pos = i
                break

        if comment_pos >= 0:
            line = line[:comment_pos].rstrip()

        lines.append(line)

    # Join lines and parse JSON
    json_str = '\n'.join(lines)

    # Remove trailing commas before } and ]
    import re
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

    return json.loads(json_str)

def load_template() -> str:
    """Load theme template as string."""
    template_path = Path(__file__).parent / 'templates' / 'theme-template.json'
    with open(template_path, 'r') as f:
        return f.read()

def replace_colors(template: str, palette: Dict[str, Any]) -> str:
    """Replace color placeholders in template with actual colors."""
    result = template

    # Replace theme name
    result = result.replace('{{theme_name}}', palette['name'])

    # Replace appearance (default to dark if not specified)
    appearance = palette.get('appearance', 'dark')
    result = result.replace('{{appearance}}', appearance)

    # Replace all color placeholders
    for key, value in palette['colors'].items():
        placeholder = f'{{{{{key}}}}}'
        result = result.replace(placeholder, value)

    return result

def parse_theme_json(theme_str: str) -> Dict[str, Any]:
    """Parse theme JSON string, removing comments."""
    # Remove single-line comments
    lines = []
    for line in theme_str.split('\n'):
        # Find comment position, but ignore // inside strings
        comment_pos = -1
        in_string = False
        escape_next = False

        for i, char in enumerate(line):
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
            if not in_string and line[i:i+2] == '//':
                comment_pos = i
                break

        if comment_pos >= 0:
            line = line[:comment_pos].rstrip()

        if line.strip():  # Only add non-empty lines
            lines.append(line)

    # Join lines and parse JSON
    json_str = '\n'.join(lines)

    # Remove trailing commas before } and ]
    import re
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

    return json.loads(json_str)

def load_existing_themes() -> Dict[str, Any]:
    """Load existing themes file or create new structure."""
    themes_file = Path(__file__).parent / 'themes' / 'fedaykin-themes.json'

    if themes_file.exists():
        with open(themes_file, 'r') as f:
            return json.load(f)
    else:
        # Create initial structure
        return {
            "name": "Fedaykin Themes",
            "author": "FedaykinDev",
            "themes": []
        }

def add_or_update_theme(themes_data: Dict[str, Any], new_theme: Dict[str, Any]) -> None:
    """Add new theme or update existing one in themes array."""
    theme_name = new_theme['name']

    # Find and replace existing theme with same name
    for i, theme in enumerate(themes_data['themes']):
        if theme['name'] == theme_name:
            themes_data['themes'][i] = new_theme
            print(f"Updated existing theme: {theme_name}")
            return

    # Add new theme if not found
    themes_data['themes'].append(new_theme)
    print(f"Added new theme: {theme_name}")

def save_themes(themes_data: Dict[str, Any]) -> None:
    """Save themes to file."""
    themes_file = Path(__file__).parent / 'themes' / 'fedaykin-themes.json'

    # Ensure themes directory exists
    themes_file.parent.mkdir(exist_ok=True)

    with open(themes_file, 'w') as f:
        json.dump(themes_data, f, indent=2)

    print(f"Saved to: {themes_file}")
    print(f"Total themes: {len(themes_data['themes'])}")

def generate_theme(palette_path: str) -> None:
    """Generate theme from palette file."""
    # Load palette
    palette = load_palette(palette_path)
    print(f"Generating theme: {palette['name']}")

    # Load template
    template = load_template()

    # Replace colors
    theme_str = replace_colors(template, palette)

    # Parse theme JSON (removes comments)
    try:
        new_theme = parse_theme_json(theme_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing generated theme JSON: {e}")
        print("Generated theme string (first 500 chars):")
        print(theme_str[:500])
        sys.exit(1)

    # Load existing themes
    themes_data = load_existing_themes()

    # Add or update theme
    add_or_update_theme(themes_data, new_theme)

    # Save themes
    save_themes(themes_data)

def list_themes() -> None:
    """List all themes in the themes file."""
    themes_data = load_existing_themes()

    print("\nCurrent themes:")
    for i, theme in enumerate(themes_data['themes'], 1):
        print(f"   {i}. {theme['name']} ({theme['appearance']})")

    if not themes_data['themes']:
        print("   No themes found.")

def remove_theme(theme_name: str) -> None:
    """Remove a theme by name."""
    themes_data = load_existing_themes()

    initial_count = len(themes_data['themes'])
    themes_data['themes'] = [t for t in themes_data['themes'] if t['name'] != theme_name]

    if len(themes_data['themes']) < initial_count:
        save_themes(themes_data)
        print(f"Removed theme: {theme_name}")
    else:
        print(f"Theme not found: {theme_name}")

def regenerate_all_themes() -> None:
    """Regenerate all themes from color palette files."""
    color_palettes_dir = Path(__file__).parent / 'color_palettes'

    if not color_palettes_dir.exists():
        print("Color palettes directory not found!")
        sys.exit(1)

    # Find all palette files (excluding template)
    palette_files = []
    for palette_file in color_palettes_dir.glob('*.json'):
        if palette_file.name != 'palette-template.json':
            palette_files.append(palette_file)

    if not palette_files:
        print("No palette files found!")
        return

    print(f"Found {len(palette_files)} palette files")

    # Create fresh themes structure
    themes_data = {
        "name": "Fedaykin Themes",
        "author": "FedaykinDev",
        "themes": []
    }

    # Load template once
    template = load_template()

    # Generate themes from all palettes
    for palette_file in sorted(palette_files):
        try:
            print(f"Processing: {palette_file.name}")

            # Load palette
            palette = load_palette(str(palette_file))

            # Replace colors in template
            theme_str = replace_colors(template, palette)

            # Parse theme JSON (removes comments)
            new_theme = parse_theme_json(theme_str)

            # Add to themes array
            themes_data['themes'].append(new_theme)

        except Exception as e:
            print(f"Error processing {palette_file.name}: {e}")
            continue

    # Save all themes
    save_themes(themes_data)
    print(f"\nSuccessfully regenerated {len(themes_data['themes'])} themes")

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_theme.py <palette.json>     - Generate theme from palette")
        print("  python generate_theme.py --list             - List all themes")
        print("  python generate_theme.py --remove <name>    - Remove theme by name")
        print("  python generate_theme.py --regenerate-all   - Regenerate all themes from color palettes")
        sys.exit(1)

    command = sys.argv[1]

    if command == '--list':
        list_themes()
    elif command == '--remove':
        if len(sys.argv) < 3:
            print("Please provide theme name to remove")
            sys.exit(1)
        remove_theme(sys.argv[2])
    elif command == '--regenerate-all':
        regenerate_all_themes()
    else:
        # Assume it's a palette file path
        palette_path = Path(command)
        if not palette_path.exists():
            print(f"Palette file not found: {palette_path}")
            sys.exit(1)

        generate_theme(str(palette_path))

if __name__ == "__main__":
    main()
