"""
MatsushibaDB - Next-Generation SQL Database by Matsushiba Systems
Complete enterprise database solution with client and server functionality.
"""

__version__ = "1.0.8"
__author__ = "Matsushiba Systems"
__email__ = "support@matsushiba.co"
__license__ = "Commercial"

from .client import MatsushibaDBClient
from .async_client import AsyncMatsushibaDBClient
from .server import MatsushibaDBServer

__all__ = ["MatsushibaDBClient", "AsyncMatsushibaDBClient", "MatsushibaDBServer"]
