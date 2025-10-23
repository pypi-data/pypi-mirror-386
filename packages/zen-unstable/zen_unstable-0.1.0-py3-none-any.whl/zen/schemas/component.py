"""
JSON-based component schema for zen-unstable.
"""

import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from pathlib import Path

class ComponentFile(BaseModel):
    """Represents a file in a component with embedded content."""
    name: str = Field(..., description="Name of the file")
    path: str = Field(..., description="Target path where file should be installed")
    content: str = Field(..., description="File content (embedded)")

class ComponentSchema(BaseModel):
    """JSON schema for component definitions."""
    name: str = Field(..., description="Component name")
    version: str = Field(..., description="Component version")
    description: str = Field(..., description="Component description")
    category: str = Field(default="utils", description="Component category")
    type: str = Field(default="component", description="Component type")
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list, description="Python package dependencies")
    dev_dependencies: List[str] = Field(default_factory=list, description="Development dependencies")
    registry_dependencies: List[str] = Field(default_factory=list, description="Other component dependencies")
    
    # Files with embedded content
    files: List[ComponentFile] = Field(..., description="List of files with embedded content")
    
    # Metadata
    author: Optional[str] = Field(None, description="Component author")
    license: Optional[str] = Field(None, description="Component license")
    python_requires: Optional[str] = Field(None, description="Python version requirement")
    keywords: List[str] = Field(default_factory=list, description="Component keywords")
    homepage: Optional[str] = Field(None, description="Component homepage URL")

    @validator('name')
    def validate_name(cls, v):
        """Validate component name format."""
        if not v or not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Component name must be alphanumeric with optional hyphens/underscores')
        return v.lower()

    @validator('version')
    def validate_version(cls, v):
        """Validate version format (basic semver)."""
        import re
        if not re.match(r'^\d+\.\d+\.\d+', v):
            raise ValueError('Version must follow semantic versioning (e.g., 1.0.0)')
        return v

    @validator('files')
    def validate_files(cls, v):
        """Ensure at least one file is provided."""
        if not v:
            raise ValueError('Component must have at least one file')
        return v

def load_component_from_json(json_content: str) -> ComponentSchema:
    """
    Load component from JSON string.
    
    Args:
        json_content: JSON string containing component definition
        
    Returns:
        ComponentSchema instance
        
    Raises:
        ValueError: If JSON is invalid or doesn't match schema
    """
    try:
        data = json.loads(json_content)
        return ComponentSchema(**data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    except Exception as e:
        raise ValueError(f"Invalid component schema: {e}")

def load_component_from_url(url: str) -> ComponentSchema:
    """
    Load component from JSON URL.
    
    Args:
        url: URL pointing to JSON component definition
        
    Returns:
        ComponentSchema instance
    """
    import requests
    from urllib.parse import urlparse
    
    try:
        parsed_url = urlparse(url)
        
        # Handle file:// URLs
        if parsed_url.scheme == 'file':
            file_path = parsed_url.path
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return load_component_from_json(content)
        
        # Handle HTTP/HTTPS URLs
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return load_component_from_json(response.text)
    except (requests.RequestException, FileNotFoundError, OSError) as e:
        raise ValueError(f"Failed to fetch component from {url}: {e}")

def create_sample_component_json() -> str:
    """Create a sample component JSON for testing."""
    sample = {
        "name": "email-validator",
        "version": "1.0.0",
        "description": "Simple email validation utility",
        "category": "utils",
        "type": "component",
        "dependencies": ["email-validator"],
        "files": [
            {
                "name": "validator.py",
                "path": "src/utils/validator.py",
                "content": '''"""Simple email validation utility."""
import re
from typing import Union
from email_validator import validate_email as _validate_email, EmailNotValidError

def validate_email(email: str) -> bool:
    """Validate email address using email-validator package."""
    try:
        _validate_email(email)
        return True
    except EmailNotValidError:
        return False

def extract_domain(email: str) -> Union[str, None]:
    """Extract domain from email address."""
    if validate_email(email):
        return email.split('@')[1]
    return None
'''
            },
            {
                "name": "__init__.py",
                "path": "src/utils/__init__.py", 
                "content": '''"""Email validation utilities."""
from .validator import validate_email, extract_domain
__all__ = ['validate_email', 'extract_domain']
'''
            }
        ],
        "author": "zen-unstable",
        "license": "MIT"
    }
    return json.dumps(sample, indent=2)
