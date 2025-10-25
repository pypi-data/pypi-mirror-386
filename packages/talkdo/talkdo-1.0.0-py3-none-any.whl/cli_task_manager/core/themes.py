"""
Themes and customization for the CLI Task Manager.

This module provides theme management, color schemes, and UI customization
options for a personalized user experience.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from rich.console import Console
from rich.theme import Theme


class ThemeType(str, Enum):
    """Available theme types."""
    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"
    SOLARIZED = "solarized"
    MONOKAI = "monokai"
    DRACULA = "dracula"
    NORD = "nord"
    GRUVBOX = "gruvbox"
    CUSTOM = "custom"


@dataclass
class ColorScheme:
    """Color scheme definition."""
    name: str
    description: str
    colors: Dict[str, str]
    style: str  # "light" or "dark"


class ThemeManager:
    """Manages themes and color schemes."""
    
    def __init__(self):
        """Initialize theme manager."""
        self.themes = self._load_builtin_themes()
        self.current_theme = ThemeType.AUTO
        self.custom_theme: Optional[ColorScheme] = None
    
    def _load_builtin_themes(self) -> Dict[ThemeType, ColorScheme]:
        """Load built-in themes."""
        themes = {}
        
        # Light theme
        themes[ThemeType.LIGHT] = ColorScheme(
            name="Light",
            description="Clean and bright theme for daytime use",
            colors={
                "task.pending": "blue",
                "task.in_progress": "yellow",
                "task.completed": "green",
                "task.cancelled": "red",
                "priority.urgent": "red bold",
                "priority.high": "yellow bold",
                "priority.medium": "white",
                "priority.low": "blue",
                "overdue": "red bold",
                "due_today": "yellow bold",
                "project": "cyan",
                "tag": "magenta",
                "success": "green bold",
                "warning": "yellow bold",
                "error": "red bold",
                "info": "blue",
                "dim": "dim",
                "accent": "bright_blue",
                "background": "white",
                "foreground": "black"
            },
            style="light"
        )
        
        # Dark theme
        themes[ThemeType.DARK] = ColorScheme(
            name="Dark",
            description="Dark theme for low-light environments",
            colors={
                "task.pending": "bright_blue",
                "task.in_progress": "bright_yellow",
                "task.completed": "bright_green",
                "task.cancelled": "bright_red",
                "priority.urgent": "bright_red bold",
                "priority.high": "bright_yellow bold",
                "priority.medium": "white",
                "priority.low": "bright_blue",
                "overdue": "bright_red bold",
                "due_today": "bright_yellow bold",
                "project": "bright_cyan",
                "tag": "bright_magenta",
                "success": "bright_green bold",
                "warning": "bright_yellow bold",
                "error": "bright_red bold",
                "info": "bright_blue",
                "dim": "dim",
                "accent": "bright_blue",
                "background": "black",
                "foreground": "white"
            },
            style="dark"
        )
        
        # Solarized theme
        themes[ThemeType.SOLARIZED] = ColorScheme(
            name="Solarized",
            description="Solarized color scheme for comfortable reading",
            colors={
                "task.pending": "#268bd2",  # blue
                "task.in_progress": "#b58900",  # yellow
                "task.completed": "#859900",  # green
                "task.cancelled": "#dc322f",  # red
                "priority.urgent": "#dc322f bold",  # red
                "priority.high": "#b58900 bold",  # yellow
                "priority.medium": "#93a1a1",  # base1
                "priority.low": "#268bd2",  # blue
                "overdue": "#dc322f bold",  # red
                "due_today": "#b58900 bold",  # yellow
                "project": "#2aa198",  # cyan
                "tag": "#d33682",  # magenta
                "success": "#859900 bold",  # green
                "warning": "#b58900 bold",  # yellow
                "error": "#dc322f bold",  # red
                "info": "#268bd2",  # blue
                "dim": "dim",
                "accent": "#268bd2",  # blue
                "background": "#fdf6e3",  # base3
                "foreground": "#586e75"  # base01
            },
            style="light"
        )
        
        # Monokai theme
        themes[ThemeType.MONOKAI] = ColorScheme(
            name="Monokai",
            description="Monokai color scheme inspired by Sublime Text",
            colors={
                "task.pending": "#66d9ef",  # cyan
                "task.in_progress": "#e6db74",  # yellow
                "task.completed": "#a6e22e",  # green
                "task.cancelled": "#f92672",  # red
                "priority.urgent": "#f92672 bold",  # red
                "priority.high": "#e6db74 bold",  # yellow
                "priority.medium": "#f8f8f2",  # white
                "priority.low": "#66d9ef",  # cyan
                "overdue": "#f92672 bold",  # red
                "due_today": "#e6db74 bold",  # yellow
                "project": "#a6e22e",  # green
                "tag": "#ae81ff",  # purple
                "success": "#a6e22e bold",  # green
                "warning": "#e6db74 bold",  # yellow
                "error": "#f92672 bold",  # red
                "info": "#66d9ef",  # cyan
                "dim": "dim",
                "accent": "#66d9ef",  # cyan
                "background": "#272822",  # dark
                "foreground": "#f8f8f2"  # light
            },
            style="dark"
        )
        
        # Dracula theme
        themes[ThemeType.DRACULA] = ColorScheme(
            name="Dracula",
            description="Dracula color scheme for a gothic feel",
            colors={
                "task.pending": "#8be9fd",  # cyan
                "task.in_progress": "#f1fa8c",  # yellow
                "task.completed": "#50fa7b",  # green
                "task.cancelled": "#ff5555",  # red
                "priority.urgent": "#ff5555 bold",  # red
                "priority.high": "#f1fa8c bold",  # yellow
                "priority.medium": "#f8f8f2",  # white
                "priority.low": "#8be9fd",  # cyan
                "overdue": "#ff5555 bold",  # red
                "due_today": "#f1fa8c bold",  # yellow
                "project": "#50fa7b",  # green
                "tag": "#bd93f9",  # purple
                "success": "#50fa7b bold",  # green
                "warning": "#f1fa8c bold",  # yellow
                "error": "#ff5555 bold",  # red
                "info": "#8be9fd",  # cyan
                "dim": "dim",
                "accent": "#8be9fd",  # cyan
                "background": "#282a36",  # dark
                "foreground": "#f8f8f2"  # light
            },
            style="dark"
        )
        
        # Nord theme
        themes[ThemeType.NORD] = ColorScheme(
            name="Nord",
            description="Nord color scheme for a calm and focused experience",
            colors={
                "task.pending": "#5e81ac",  # nord10
                "task.in_progress": "#ebcb8b",  # nord13
                "task.completed": "#a3be8c",  # nord14
                "task.cancelled": "#bf616a",  # nord11
                "priority.urgent": "#bf616a bold",  # nord11
                "priority.high": "#ebcb8b bold",  # nord13
                "priority.medium": "#d8dee9",  # nord6
                "priority.low": "#5e81ac",  # nord10
                "overdue": "#bf616a bold",  # nord11
                "due_today": "#ebcb8b bold",  # nord13
                "project": "#88c0d0",  # nord8
                "tag": "#b48ead",  # nord15
                "success": "#a3be8c bold",  # nord14
                "warning": "#ebcb8b bold",  # nord13
                "error": "#bf616a bold",  # nord11
                "info": "#5e81ac",  # nord10
                "dim": "dim",
                "accent": "#5e81ac",  # nord10
                "background": "#2e3440",  # nord0
                "foreground": "#d8dee9"  # nord6
            },
            style="dark"
        )
        
        # Gruvbox theme
        themes[ThemeType.GRUVBOX] = ColorScheme(
            name="Gruvbox",
            description="Gruvbox color scheme for a retro feel",
            colors={
                "task.pending": "#83a598",  # blue
                "task.in_progress": "#fabd2f",  # yellow
                "task.completed": "#b8bb26",  # green
                "task.cancelled": "#fb4934",  # red
                "priority.urgent": "#fb4934 bold",  # red
                "priority.high": "#fabd2f bold",  # yellow
                "priority.medium": "#ebdbb2",  # fg
                "priority.low": "#83a598",  # blue
                "overdue": "#fb4934 bold",  # red
                "due_today": "#fabd2f bold",  # yellow
                "project": "#8ec07c",  # green
                "tag": "#d3869b",  # purple
                "success": "#b8bb26 bold",  # green
                "warning": "#fabd2f bold",  # yellow
                "error": "#fb4934 bold",  # red
                "info": "#83a598",  # blue
                "dim": "dim",
                "accent": "#83a598",  # blue
                "background": "#282828",  # bg0
                "foreground": "#ebdbb2"  # fg
            },
            style="dark"
        )
        
        return themes
    
    def get_theme(self, theme_type: ThemeType) -> ColorScheme:
        """Get theme by type."""
        if theme_type == ThemeType.CUSTOM and self.custom_theme:
            return self.custom_theme
        return self.themes.get(theme_type, self.themes[ThemeType.DARK])
    
    def set_theme(self, theme_type: ThemeType) -> None:
        """Set current theme."""
        self.current_theme = theme_type
    
    def create_custom_theme(self, name: str, description: str, colors: Dict[str, str], style: str) -> None:
        """Create a custom theme."""
        self.custom_theme = ColorScheme(
            name=name,
            description=description,
            colors=colors,
            style=style
        )
        self.current_theme = ThemeType.CUSTOM
    
    def get_rich_theme(self, theme_type: Optional[ThemeType] = None) -> Theme:
        """Get Rich theme for console styling."""
        theme_type = theme_type or self.current_theme
        color_scheme = self.get_theme(theme_type)
        
        # Convert color scheme to Rich theme
        rich_colors = {}
        for key, color in color_scheme.colors.items():
            # Convert to Rich format
            if color.startswith('#'):
                rich_colors[key] = color
            else:
                rich_colors[key] = color
        
        return Theme(rich_colors)
    
    def list_themes(self) -> List[Dict[str, Any]]:
        """List all available themes."""
        themes = []
        for theme_type, color_scheme in self.themes.items():
            themes.append({
                "type": theme_type.value,
                "name": color_scheme.name,
                "description": color_scheme.description,
                "style": color_scheme.style
            })
        
        if self.custom_theme:
            themes.append({
                "type": "custom",
                "name": self.custom_theme.name,
                "description": self.custom_theme.description,
                "style": self.custom_theme.style
            })
        
        return themes
    
    def get_theme_preview(self, theme_type: ThemeType) -> str:
        """Get a preview of the theme colors."""
        color_scheme = self.get_theme(theme_type)
        
        preview = f"Theme: {color_scheme.name}\n"
        preview += f"Description: {color_scheme.description}\n"
        preview += f"Style: {color_scheme.style}\n\n"
        preview += "Color Preview:\n"
        
        # Show key colors
        key_colors = [
            ("task.pending", "Pending Task"),
            ("task.completed", "Completed Task"),
            ("priority.urgent", "Urgent Priority"),
            ("priority.high", "High Priority"),
            ("overdue", "Overdue Task"),
            ("project", "Project Name"),
            ("tag", "Tag Name"),
            ("success", "Success Message"),
            ("warning", "Warning Message"),
            ("error", "Error Message")
        ]
        
        for color_key, description in key_colors:
            if color_key in color_scheme.colors:
                preview += f"  {description}: {color_scheme.colors[color_key]}\n"
        
        return preview
    
    def export_theme(self, theme_type: ThemeType) -> Dict[str, Any]:
        """Export theme configuration."""
        color_scheme = self.get_theme(theme_type)
        return {
            "name": color_scheme.name,
            "description": color_scheme.description,
            "style": color_scheme.style,
            "colors": color_scheme.colors,
            "type": theme_type.value
        }
    
    def import_theme(self, theme_config: Dict[str, Any]) -> None:
        """Import theme configuration."""
        self.create_custom_theme(
            name=theme_config.get("name", "Imported Theme"),
            description=theme_config.get("description", "Imported theme"),
            colors=theme_config.get("colors", {}),
            style=theme_config.get("style", "dark")
        )
    
    def get_accessibility_theme(self) -> ColorScheme:
        """Get high contrast theme for accessibility."""
        return ColorScheme(
            name="High Contrast",
            description="High contrast theme for better accessibility",
            colors={
                "task.pending": "bright_white on blue",
                "task.in_progress": "black on yellow",
                "task.completed": "black on green",
                "task.cancelled": "white on red",
                "priority.urgent": "white on red bold",
                "priority.high": "black on yellow bold",
                "priority.medium": "white on black",
                "priority.low": "white on blue",
                "overdue": "white on red bold",
                "due_today": "black on yellow bold",
                "project": "black on cyan",
                "tag": "black on magenta",
                "success": "black on green bold",
                "warning": "black on yellow bold",
                "error": "white on red bold",
                "info": "white on blue",
                "dim": "dim",
                "accent": "white on blue",
                "background": "black",
                "foreground": "white"
            },
            style="dark"
        )
    
    def get_minimal_theme(self) -> ColorScheme:
        """Get minimal theme with reduced colors."""
        return ColorScheme(
            name="Minimal",
            description="Minimal theme with reduced visual noise",
            colors={
                "task.pending": "white",
                "task.in_progress": "yellow",
                "task.completed": "green",
                "task.cancelled": "red",
                "priority.urgent": "red",
                "priority.high": "yellow",
                "priority.medium": "white",
                "priority.low": "blue",
                "overdue": "red",
                "due_today": "yellow",
                "project": "cyan",
                "tag": "magenta",
                "success": "green",
                "warning": "yellow",
                "error": "red",
                "info": "blue",
                "dim": "dim",
                "accent": "blue",
                "background": "black",
                "foreground": "white"
            },
            style="dark"
        )
