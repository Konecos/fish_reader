import logging
import platform
from typing import Dict, Any

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)

def get_system_theme() -> str:
    """
    Detect the system theme based on the operating system.
    Returns 'dark' or 'light'.
    """
    try:
        system = platform.system()
        
        if system == "Windows":
            # Check Windows registry for dark mode setting
            import winreg
            try:
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                winreg.CloseKey(registry)
                # If value is 0, dark mode is enabled; if 1, light mode is enabled
                return 'dark' if value == 0 else 'light'
            except (OSError, ValueError):
                # Fallback to light theme if registry access fails
                logger.warning("Could not access Windows registry for theme detection, defaulting to light theme")
                return 'light'
        
        elif system == "Darwin":  # macOS
            # Check using defaults command
            from subprocess import run, PIPE
            result = run(['defaults', 'read', '-g', 'AppleInterfaceStyle'], 
                        stdout=PIPE, stderr=PIPE, text=True)
            return 'dark' if result.returncode == 0 else 'light'
        
        else:  # Linux and others
            # Try to check environment variables commonly used for theming
            import os
            gtk_theme = os.environ.get('GTK_THEME', '').lower()
            if 'dark' in gtk_theme:
                return 'dark'
            
            # Check if KDE has dark theme configured
            try:
                kde_config = QSettings(os.path.expanduser('~/.config/kdeglobals'), QSettings.Format.IniFormat)
                color_scheme = kde_config.value('General/ColorScheme', '')
                if 'dark' in color_scheme.lower() or 'breeze' in color_scheme.lower():
                    return 'dark'
            except:
                pass
            
            # Default to light theme for other systems
            return 'light'
    
    except Exception as e:
        logger.error(f"Error detecting system theme: {e}")
        return 'light'

def get_current_theme() -> str:
    """
    Get the current theme based on the configuration and system settings.
    If theme is set to 'auto', detect the system theme.
    """
    from .config import config  # Import here to avoid circular import
    config_theme = config.get('theme', 'auto')
    
    if config_theme == 'auto':
        return get_system_theme()
    else:
        return config_theme

def get_theme_colors(theme: str = None) -> Dict[str, Any]:
    """
    Get the color settings for the specified theme or the current theme.
    """
    from .config import config  # Import here to avoid circular import
    if theme is None:
        theme = get_current_theme()
    
    # Find the theme in the themes list
    themes = config['themes']
    target_theme = None
    
    for t in themes:
        if t["name"] == theme:
            target_theme = t
            break
    
    # If the theme was not found, use defaults based on theme name
    if target_theme is None:
        if theme == 'dark':
            target_theme = {
                'name': 'dark',
                'bg': 'rgba(30, 30, 30, 240)',
                'border': '#555',
                'text': '#ddd',
                'blur_bg': 'rgba(30, 30, 30, 26)',
                'blur_text': '#dddddd22'
            }
        else:  # default to light
            target_theme = {
                'name': 'light',
                'bg': 'rgba(255, 255, 255, 240)',
                'border': '#2196F3',
                'text': '#333',
                'blur_bg': 'rgba(255, 255, 255, 26)',
                'blur_text': '#33333322'
            }
    
    # Return the color settings for the found or default theme
    return {
        'bg_color': getattr(target_theme, 'bg', target_theme.get('bg', 'rgba(255, 255, 255, 240)')),
        'border_color': getattr(target_theme, 'border', target_theme.get('border', '#2196F3')),
        'text_color': getattr(target_theme, 'text', target_theme.get('text', '#333')),
        'blur_bg_color': getattr(target_theme, 'blur_bg', target_theme.get('blur_bg', 'rgba(255, 255, 255, 26)')),
        'blur_text_color': getattr(target_theme, 'blur_text', target_theme.get('blur_text', '#33333322')),
    }

def apply_theme_to_app(app: QApplication):
    """
    Apply the appropriate theme to the Qt application based on the current configuration.
    """
    theme = get_current_theme()
    
    # Create a simple dark or light palette
    if theme == 'dark':
        app.setStyle("Fusion")  # Use Fusion for consistent dark theme
        palette = app.palette()
        palette.setColor(app.palette().ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(app.palette().ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(app.palette().ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(app.palette().ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(app.palette().ColorRole.ToolTipBase, QColor(0, 0, 0))
        palette.setColor(app.palette().ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(app.palette().ColorRole.Text, QColor(230, 230, 230))
        palette.setColor(app.palette().ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(app.palette().ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(app.palette().ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(app.palette().ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(app.palette().ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(app.palette().ColorRole.HighlightedText, QColor(0, 0, 0))
        app.setPalette(palette)
    else:  # light theme
        # Reset to default palette
        app.setPalette(app.style().standardPalette())
