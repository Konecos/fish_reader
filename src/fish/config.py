import logging
import os
import sys
from pathlib import Path
from typing import Literal, Optional, List

from configium import ConfigManager
from pydantic import BaseModel, Field
from configium.exceptions import ValidationError

app_data_dir = Path(os.getenv('APPDATA')) / "fish"
app_data_dir.mkdir(exist_ok=True, parents=True)

bookshelf = ConfigManager(app_data_dir / "bookshelf.json", auto_save=False, auto_reload=False)


class ThemeSchema(BaseModel):
    name: str = Field(default="light", description="Name of the theme")
    bg: str = Field(default="rgba(255, 255, 255, 240)", description="Background color when focused")
    border: str = Field(default="#2196F3", description="Border color")
    text: str = Field(default="#333", description="Text color")
    blur_bg: str = Field(default="rgba(255, 255, 255, 26)", description="Background color when blurred")
    blur_text: str = Field(default="#33333322", description="Text color when blurred")


class ConfigModel(BaseModel):
    # Theme settings
    theme: Literal['auto', 'dark', 'light'] = 'auto'
    
    # Available themes
    themes: List[ThemeSchema] = Field(default_factory=lambda: [
        ThemeSchema(
            name="light",
            bg="rgba(255, 255, 255, 240)",
            border="#2196F3",
            text="#333",
            blur_bg="rgba(255, 255, 255, 26)",
            blur_text="#33333322"
        ),
        ThemeSchema(
            name="dark",
            bg="rgba(30, 30, 30, 240)",
            border="#555",
            text="#ddd",
            blur_bg="rgba(30, 30, 30, 26)",
            blur_text="#dddddd22"
        )
    ])
    
    # Window settings
    window_width: int = Field(default=500, ge=200, le=2000, description="Window width in pixels")
    window_height: int = Field(default=75, ge=50, le=1000, description="Window height in pixels")
    window_x: Optional[int] = Field(default=None, description="Window x position")
    window_y: Optional[int] = Field(default=None, description="Window y position")
    
    # Font settings
    font_family: str = Field(default="Microsoft YaHei", description="Font family for the display")
    font_size: int = Field(default=10, ge=6, le=30, description="Font size for the display")
    
    # Book reading settings
    lines_per_page: int = Field(default=1, ge=1, le=10, description="Number of lines to display per page")
    auto_save_progress: bool = Field(default=True, description="Automatically save reading progress")
    
    # UI settings
    opacity_when_focused: float = Field(default=0.95, ge=0.1, le=1.0, description="Opacity when window is focused")
    opacity_when_blurred: float = Field(default=0.1, ge=0.0, le=1.0, description="Opacity when window is blurred")


config_file = app_data_dir / "config.yaml"
try:
    config = ConfigManager(config_file, validation_model=ConfigModel, auto_reload=False)
    config.save()
except ValidationError as e:
    logging.error(f"%s validation error: %s", config_file, e)
    sys.exit(1)

