#!/usr/bin/env python3
"""
zen-unstable CLI - Python component registry like shadcn/ui
"""

import click
import sys
from pathlib import Path
from zen.core.logger import get_logger, setup_logging
from zen.core.installer import ComponentInstaller
from zen.core.exceptions import InstallationError, ConfigurationError

logger = get_logger()

@click.group()
@click.version_option(version="0.1.0", prog_name="zen-unstable")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose):
    """zen-unstable - Python component registry like shadcn/ui"""
    setup_logging(verbose=verbose)

@cli.command()
@click.argument("project_name", required=False)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing project")
def init(project_name, force):
    """Initialize a new zen project"""
    try:
        project_path = Path(project_name) if project_name else Path.cwd()
        
        if project_name:
            if project_path.exists() and not force:
                logger.error(f"Directory '{project_name}' already exists. Use --force to overwrite.")
                sys.exit(1)
            
            project_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created project directory: {project_path}")
        
        # Create project structure
        _create_project_structure(project_path)
        
        logger.success("✨ Successfully initialized zen project")
        logger.info(f"Project location: {project_path.resolve()}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. cd into your project directory")
        logger.info("  2. Run 'zen add <component-url>' to install components")
        logger.info("  3. Install dependencies with 'pip install -r requirements.txt'")
        
    except Exception as e:
        logger.error(f"Failed to initialize project: {e}")
        sys.exit(1)

@cli.command()
@click.argument("component_url")
@click.option("--path", "-p", help="Custom installation path")
@click.option("--overwrite", "-o", is_flag=True, help="Overwrite existing files")
@click.option("--dry-run", "-d", is_flag=True, help="Show what would be done without doing it")
def add(component_url, path, overwrite, dry_run):
    """Install a component from JSON URL"""
    try:
        # Check if we're in a zen project
        if not Path(".zen/config.yaml").exists():
            logger.error("Not in a zen project. Run 'zen init' first.")
            sys.exit(1)
        
        installer = ComponentInstaller()
        
        if dry_run:
            logger.info("🔍 DRY RUN - No changes will be made")
            logger.info(f"Would install component from: {component_url}")
            if path:
                logger.info(f"Would install to: {path}")
            return
        
        # Install component
        result = installer.install_from_url(component_url, path, overwrite)
        
        # Show success message
        logger.success(f"✨ Successfully installed {result['component']}")
        logger.info(f"Files installed: {result['files_installed']}")
        logger.info(f"Dependencies added: {result['dependencies_added']}")
        logger.info(f"Install path: {result['install_path']}")
        logger.info("")
        logger.info("🎉 Component is ready to use!")
        logger.info("💡 Run 'pip install -r requirements.txt' to install dependencies")
        
    except (InstallationError, ConfigurationError) as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

def _create_project_structure(project_path: Path):
    """Create the basic project structure"""
    import yaml
    
    # Create directories
    directories = [
        ".zen",
        "src",
        "src/components", 
        "src/utils",
        "src/models",
        "src/services",
        "src/auth",
        "src/data"
    ]
    
    for dir_name in directories:
        dir_path = project_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {dir_path}")
    
    # Create config file
    config = {
        "name": project_path.name,
        "version": "1.0.0",
        "description": f"zen-unstable project: {project_path.name}",
        "structure": {
            "components": "src/components",
            "utils": "src/utils", 
            "models": "src/models",
            "services": "src/services",
            "auth": "src/auth",
            "data": "src/data"
        },
        "components": {}
    }
    
    config_path = project_path / ".zen" / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    logger.info(f"Created configuration file: {config_path}")
    
    # Create requirements.txt
    requirements_path = project_path / "requirements.txt"
    with open(requirements_path, "w") as f:
        f.write("# Project dependencies\n")
    logger.info("Created requirements.txt")
    
    # Create .gitignore
    gitignore_path = project_path / ".gitignore"
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
.zen/cache/
"""
    with open(gitignore_path, "w") as f:
        f.write(gitignore_content)
    logger.info("Created .gitignore")
    
    # Create README.md
    readme_path = project_path / "README.md"
    readme_content = f"""# {project_path.name}

A zen-unstable project.

## Installation

Install dependencies:
```bash
pip install -r requirements.txt
```

## Adding Components

Install components from JSON URLs:
```bash
zen add https://example.com/component.json
zen add https://github.com/user/repo/component.json
```

## Project Structure

```
{project_path.name}/
├── src/
│   ├── components/    # General components
│   ├── utils/         # Utility functions
│   ├── models/        # Data models
│   ├── services/      # Business logic
│   ├── auth/          # Authentication
│   └── data/          # Data processing
├── .zen/
│   └── config.yaml    # Project configuration
├── requirements.txt   # Python dependencies
└── README.md
```

Built with [zen-unstable](https://github.com/TheRaj71/Zenive-Unstable)
"""
    with open(readme_path, "w") as f:
        f.write(readme_content)
    logger.info("Created README.md")
    
    # Create __init__.py files
    init_files = [
        "src/__init__.py",
        "src/components/__init__.py",
        "src/utils/__init__.py", 
        "src/models/__init__.py",
        "src/services/__init__.py",
        "src/auth/__init__.py",
        "src/data/__init__.py"
    ]
    
    for init_file in init_files:
        init_path = project_path / init_file
        with open(init_path, "w") as f:
            f.write("")
        logger.debug(f"Created {init_path}")

def main():
    """Entry point for the CLI"""
    cli()

if __name__ == "__main__":
    main()
