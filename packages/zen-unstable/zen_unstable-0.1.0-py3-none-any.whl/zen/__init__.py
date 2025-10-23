"""
zen-unstable - Python component registry like shadcn/ui
"""

__version__ = "0.1.0"
__author__ = "TheRaj71"
__description__ = "Python component registry system - like shadcn/ui for Python"

# Core imports
from zen.core.exceptions import InstallationError, ConfigurationError
from zen.schemas.component import ComponentSchema, load_component_from_json, load_component_from_url

__all__ = [
    "InstallationError",
    "ConfigurationError", 
    "ComponentSchema",
    "load_component_from_json",
    "load_component_from_url"
]
