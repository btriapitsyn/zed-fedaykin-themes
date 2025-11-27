#!/usr/bin/env python3
"""
Zed Theme Generator for Fedaykin Themes

This script generates Zed themes from color palette files.
It manages multiple themes in a single themes/fedaykin-themes.json file.
"""

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Transparency suffixes for blurred variant
# Format: hex alpha suffix (00=transparent, FF=opaque)
#
# Hex alpha reference:
#   00 = 0%    40 = 25%   80 = 50%   BF = 75%   FF = 100%
#   1A = 10%   4D = 30%   99 = 60%   CC = 80%
#   33 = 20%   66 = 40%   B3 = 70%   E6 = 90%
#
# Lower = more transparent (blur visible)
# Higher = more opaque (solid color)
#
# NOTE: Values above ~15% (26) become barely transparent.
# For good blur effect, stick to: transparent (00), ghost (0D), light (26)
#
BLUR_ALPHA = {
    "transparent": "00",  # 0% - editor/terminal/panel
    "subtle": "1A",  # 10% - borders, highlights
    "tint": "33",  # 20% - git status, search
    "visible": "60",  # 38% - ghost elements
    "solid": "A0",  # 63% - scrollbar, active tab
    "opaque": "D7",  # 84% - window frame
}

# Keys to modify for blurred variant and their transparency level
# Based on Catppuccin Blur analysis
#
BLUR_KEYS = {
    # Window frame - nearly opaque (84%)
    "background": "opaque",
    "status_bar.background": "opaque",
    "title_bar.background": "opaque",
    "surface.background": "opaque",
    # Editor/terminal/panel - fully transparent for max blur
    "editor.background": "transparent",
    "editor.gutter.background": "transparent",
    "editor.active_line.background": "subtle",
    "terminal.background": "transparent",
    "panel.background": "transparent",
    "panel.overlay_background": "transparent",
    # Tab hierarchy: bar/inactive transparent, active solid
    "tab_bar.background": "transparent",
    "tab.inactive_background": "transparent",
    "tab.active_background": "solid",
    "toolbar.background": "transparent",
    # Element states
    "element.active": "transparent",
    "element.selected": "visible",
    # Borders - subtle
    "border": "subtle",
    "border.variant": "transparent",
    "border.transparent": "transparent",
    "panel.focused_border": "transparent",
    "pane.focused_border": "subtle",
    "pane_group.border": "subtle",
    # Editor elements
    "editor.highlighted_line.background": "subtle",
    "editor.line_number": "solid",
    "editor.active_line_number": "solid",
    "editor.invisible": "visible",
    "editor.wrap_guide": "subtle",
    "editor.active_wrap_guide": "tint",
    "editor.indent_guide": "solid",
    "editor.indent_guide_active": "solid",
    "editor.document_highlight.bracket_background": "subtle",
    "editor.document_highlight.read_background": "tint",
    "editor.document_highlight.write_background": "tint",
    "editor.debugger_active_line.background": "subtle",
    # Ghost elements
    "ghost_element.background": "visible",
    "ghost_element.hover": "solid",
    "ghost_element.active": "tint",
    "ghost_element.selected": "visible",
    # Scrollbar
    "scrollbar.track.background": "transparent",
    "scrollbar.track.border": "transparent",
    "scrollbar.thumb.background": "solid",
    "scrollbar.thumb.hover_background": "solid",
    "scrollbar.thumb.active_background": "solid",
    # Minimap
    "minimap.thumb.background": "tint",
    "minimap.thumb.hover_background": "visible",
    "minimap.thumb.active_background": "solid",
    # Search/highlights
    "search.match_background": "tint",
    "drop_target.background": "solid",
    # Git/VCS status backgrounds
    "conflict.background": "tint",
    "created.background": "tint",
    "deleted.background": "tint",
    "modified.background": "tint",
    "renamed.background": "tint",
    "ignored.background": "tint",
    "unreachable.background": "subtle",
    # Hints
    "hint.background": "opaque",
}


def add_alpha_to_color(color: str, alpha_level: str) -> str:
    """Add alpha suffix to hex color.

    Args:
        color: Hex color like "#RRGGBB" or "#RRGGBBAA"
        alpha_level: Key from BLUR_ALPHA dict

    Returns:
        Color with alpha suffix like "#RRGGBBCC"
    """
    if not color or not isinstance(color, str) or not color.startswith("#"):
        return color

    # Strip existing alpha if present (handle #RRGGBB and #RRGGBBAA)
    base_color = color[:7] if len(color) >= 7 else color
    alpha_suffix = BLUR_ALPHA.get(alpha_level, "FF")

    return f"{base_color}{alpha_suffix}"


def create_blurred_variant(theme: Dict[str, Any]) -> Dict[str, Any]:
    """Create blurred variant from opaque theme.

    Args:
        theme: Original opaque theme dict

    Returns:
        New theme dict with blur effect and transparency
    """
    blurred = copy.deepcopy(theme)

    # Update name
    blurred["name"] = f"{theme['name']} - blurred"

    # Add blur appearance
    blurred["style"]["background.appearance"] = "blurred"

    # Apply transparency to specified keys
    for key, alpha_level in BLUR_KEYS.items():
        if key in blurred["style"]:
            original = blurred["style"][key]
            blurred["style"][key] = add_alpha_to_color(original, alpha_level)

    return blurred


def load_palette(palette_path: str) -> Dict[str, Any]:
    """Load color palette from JSON file (with comment support)."""
    with open(palette_path, "r") as f:
        content = f.read()

    # Remove single-line comments
    lines = []
    for line in content.split("\n"):
        # Find comment position, but ignore // inside strings
        comment_pos = -1
        in_string = False
        escape_next = False

        for i, char in enumerate(line):
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
            if not in_string and line[i : i + 2] == "//":
                comment_pos = i
                break

        if comment_pos >= 0:
            line = line[:comment_pos].rstrip()

        lines.append(line)

    # Join lines and parse JSON
    json_str = "\n".join(lines)

    # Remove trailing commas before } and ]
    import re

    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

    return json.loads(json_str)


def load_template() -> str:
    """Load theme template as string."""
    template_path = Path(__file__).parent / "templates" / "theme-template.json"
    with open(template_path, "r") as f:
        return f.read()


def replace_colors(template: str, palette: Dict[str, Any]) -> str:
    """Replace color placeholders in template with actual colors."""
    result = template

    # Replace theme name
    result = result.replace("{{theme_name}}", palette["name"])

    # Replace appearance (default to dark if not specified)
    appearance = palette.get("appearance", "dark")
    result = result.replace("{{appearance}}", appearance)

    # Replace all color placeholders
    for key, value in palette["colors"].items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, value)

    return result


def parse_theme_json(theme_str: str) -> Dict[str, Any]:
    """Parse theme JSON string, removing comments."""
    # Remove single-line comments
    lines = []
    for line in theme_str.split("\n"):
        # Find comment position, but ignore // inside strings
        comment_pos = -1
        in_string = False
        escape_next = False

        for i, char in enumerate(line):
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
            if not in_string and line[i : i + 2] == "//":
                comment_pos = i
                break

        if comment_pos >= 0:
            line = line[:comment_pos].rstrip()

        if line.strip():  # Only add non-empty lines
            lines.append(line)

    # Join lines and parse JSON
    json_str = "\n".join(lines)

    # Remove trailing commas before } and ]
    import re

    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

    return json.loads(json_str)


def load_existing_themes() -> Dict[str, Any]:
    """Load existing themes file or create new structure."""
    themes_file = Path(__file__).parent / "themes" / "fedaykin-themes.json"

    if themes_file.exists():
        with open(themes_file, "r") as f:
            return json.load(f)
    else:
        # Create initial structure
        return {"name": "Fedaykin Themes", "author": "FedaykinDev", "themes": []}


def add_or_update_theme(themes_data: Dict[str, Any], new_theme: Dict[str, Any]) -> None:
    """Add new theme or update existing one in themes array."""
    theme_name = new_theme["name"]

    # Find and replace existing theme with same name
    for i, theme in enumerate(themes_data["themes"]):
        if theme["name"] == theme_name:
            themes_data["themes"][i] = new_theme
            print(f"Updated existing theme: {theme_name}")
            return

    # Add new theme if not found
    themes_data["themes"].append(new_theme)
    print(f"Added new theme: {theme_name}")


def save_themes(themes_data: Dict[str, Any]) -> None:
    """Save themes to file."""
    themes_file = Path(__file__).parent / "themes" / "fedaykin-themes.json"

    # Ensure themes directory exists
    themes_file.parent.mkdir(exist_ok=True)

    with open(themes_file, "w") as f:
        json.dump(themes_data, f, indent=2)

    print(f"Saved to: {themes_file}")
    print(f"Total themes: {len(themes_data['themes'])}")


def generate_theme(palette_path: str) -> None:
    """Generate theme from palette file (opaque + blurred variants)."""
    # Load palette
    palette = load_palette(palette_path)
    print(f"Generating theme: {palette['name']}")

    # Load template
    template = load_template()

    # Replace colors
    theme_str = replace_colors(template, palette)

    # Parse theme JSON (removes comments)
    try:
        opaque_theme = parse_theme_json(theme_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing generated theme JSON: {e}")
        print("Generated theme string (first 500 chars):")
        print(theme_str[:500])
        sys.exit(1)

    # Create blurred variant
    blurred_theme = create_blurred_variant(opaque_theme)

    # Load existing themes
    themes_data = load_existing_themes()

    # Add or update both variants
    add_or_update_theme(themes_data, opaque_theme)
    add_or_update_theme(themes_data, blurred_theme)

    # Save themes
    save_themes(themes_data)


def list_themes() -> None:
    """List all themes in the themes file."""
    themes_data = load_existing_themes()

    print("\nCurrent themes:")
    for i, theme in enumerate(themes_data["themes"], 1):
        print(f"   {i}. {theme['name']} ({theme['appearance']})")

    if not themes_data["themes"]:
        print("   No themes found.")


def remove_theme(theme_name: str) -> None:
    """Remove a theme by name."""
    themes_data = load_existing_themes()

    initial_count = len(themes_data["themes"])
    themes_data["themes"] = [
        t for t in themes_data["themes"] if t["name"] != theme_name
    ]

    if len(themes_data["themes"]) < initial_count:
        save_themes(themes_data)
        print(f"Removed theme: {theme_name}")
    else:
        print(f"Theme not found: {theme_name}")


def regenerate_all_themes() -> None:
    """Regenerate all themes from color palette files (opaque + blurred)."""
    color_palettes_dir = Path(__file__).parent / "color_palettes"

    if not color_palettes_dir.exists():
        print("Color palettes directory not found!")
        sys.exit(1)

    # Find all palette files (excluding template)
    palette_files = []
    for palette_file in color_palettes_dir.glob("*.json"):
        if palette_file.name != "palette-template.json":
            palette_files.append(palette_file)

    if not palette_files:
        print("No palette files found!")
        return

    print(f"Found {len(palette_files)} palette files")
    print(f"Will generate {len(palette_files) * 2} themes (opaque + blurred)\n")

    # Create fresh themes structure
    themes_data = {"name": "Fedaykin Themes", "author": "FedaykinDev", "themes": []}

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
            opaque_theme = parse_theme_json(theme_str)

            # Create blurred variant
            blurred_theme = create_blurred_variant(opaque_theme)

            # Add both variants to themes array
            themes_data["themes"].append(opaque_theme)
            themes_data["themes"].append(blurred_theme)

            print(f"  + {opaque_theme['name']}")
            print(f"  + {blurred_theme['name']}")

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
        print(
            "  python generate_theme.py <palette.json>     - Generate theme from palette"
        )
        print("  python generate_theme.py --list             - List all themes")
        print("  python generate_theme.py --remove <name>    - Remove theme by name")
        print(
            "  python generate_theme.py --regenerate-all   - Regenerate all themes from color palettes"
        )
        sys.exit(1)

    command = sys.argv[1]

    if command == "--list":
        list_themes()
    elif command == "--remove":
        if len(sys.argv) < 3:
            print("Please provide theme name to remove")
            sys.exit(1)
        remove_theme(sys.argv[2])
    elif command == "--regenerate-all":
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
