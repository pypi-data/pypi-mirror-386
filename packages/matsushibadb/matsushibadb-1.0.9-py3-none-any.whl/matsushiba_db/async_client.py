"""
MatsushibaDB Async Python client library
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional

class AsyncMatsushibaDBClient:
    """Async MatsushibaDB client"""
    
    def __init__(self, host: str = "localhost", port: int = 8000, api_key: Optional[str] = None):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.base_url = f"http://{host}:{port}"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def execute(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute SQL query asynchronously"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        data = {"sql": sql}
        if params:
            data["params"] = params
        
        async with self.session.post(f"{self.base_url}/query", json=data, headers=headers) as response:
            return await response.json()
    
    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None
