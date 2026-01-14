"""
MALDB - A minimal relational database management system
"""

__version__ = "0.1.0"
__author__ = "Mal-archLumi"

from .core.database import Database
from .api.server import start_api_server
from .repl.shell import start_repl

__all__ = ['Database', 'start_api_server', 'start_repl']