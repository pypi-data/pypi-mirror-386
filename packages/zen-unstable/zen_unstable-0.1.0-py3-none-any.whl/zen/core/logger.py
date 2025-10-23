"""
Logging configuration for Zenive.
"""

import logging
import sys
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text


class ZeniveLogger:
    """Custom logger for Zenive with rich formatting."""
    
    def __init__(self, name: str = "zenive", level: int = logging.INFO):
        self.console = Console()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create rich handler
        rich_handler = RichHandler(
            console=self.console,
            show_time=False,
            show_path=False,
            markup=True,
        )
        rich_handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter("%(message)s")
        rich_handler.setFormatter(formatter)
        
        self.logger.addHandler(rich_handler)
        self.logger.propagate = False
    
    def info(self, message: str, **kwargs):
        """Log info message with rich formatting."""
        self.logger.info(f"[blue]ℹ[/blue] {message}", **kwargs)
    
    def success(self, message: str, **kwargs):
        """Log success message with rich formatting."""
        self.logger.info(f"[green]✓[/green] {message}", **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with rich formatting."""
        self.logger.warning(f"[yellow]⚠[/yellow] {message}", **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with rich formatting."""
        self.logger.error(f"[red]✗[/red] {message}", **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with rich formatting."""
        self.logger.debug(f"[dim]🐛[/dim] {message}", **kwargs)
    
    def step(self, message: str, **kwargs):
        """Log step message for processes."""
        self.logger.info(f"[cyan]→[/cyan] {message}", **kwargs)
    
    def progress(self, message: str, **kwargs):
        """Log progress message."""
        self.logger.info(f"[magenta]⟳[/magenta] {message}", **kwargs)


# Global logger instance
_logger: Optional[ZeniveLogger] = None


def get_logger(name: str = "zenive", level: int = logging.INFO) -> ZeniveLogger:
    """Get or create the global Zenive logger."""
    global _logger
    if _logger is None:
        _logger = ZeniveLogger(name, level)
    return _logger


def set_log_level(level: int):
    """Set the logging level for the global logger."""
    logger = get_logger()
    logger.logger.setLevel(level)
    for handler in logger.logger.handlers:
        handler.setLevel(level)


def enable_debug():
    """Enable debug logging."""
    set_log_level(logging.DEBUG)


def disable_debug():
    """Disable debug logging."""
    set_log_level(logging.INFO)

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    set_log_level(level)
