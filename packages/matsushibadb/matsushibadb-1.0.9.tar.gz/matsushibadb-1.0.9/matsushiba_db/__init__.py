"""
MatsushibaDB - Next-Generation SQL Database by Matsushiba Systems
Complete enterprise database solution with client and server functionality.
"""

__version__ = "1.0.9"
__author__ = "Matsushiba Systems"
__email__ = "support@matsushiba.co"
__license__ = "Commercial"

from .client import MatsushibaDBClient
from .async_client import AsyncMatsushibaDBClient
from .server import MatsushibaDBServer
from .enhanced_client import MatsushibaDBClient as EnhancedMatsushibaDBClient
from .internal_abstraction import MatsushibaDBInternal

__all__ = [
    "MatsushibaDBClient", 
    "AsyncMatsushibaDBClient", 
    "MatsushibaDBServer",
    "EnhancedMatsushibaDBClient",
    "MatsushibaDBInternal"
]
