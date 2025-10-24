#!/usr/bin/env python3
"""
MatsushibaDB - Enhanced Python Client Library
A feature-rich client for Python applications with async support
"""

import json
import socket
import ssl
import asyncio
import aiohttp
import requests
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urljoin
import base64
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum


class Protocol(Enum):
    """Supported protocols."""
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"


@dataclass
class ClientConfig:
    """Client configuration."""
    protocol: Protocol = Protocol.HTTP
    host: str = "localhost"
    port: int = 8000
    api_key: Optional[str] = None
    timeout: int = 30
    ssl_verify: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    connection_pool_size: int = 10


class MatsushibaDBClient:
    """Enhanced MatsushibaDB client with async support."""
    
    def __init__(self, config: ClientConfig):
        self.config = config
        self.session = None
        self.logger = logging.getLogger(__name__)
        
        # Set default ports based on protocol
        if config.port == 8000:
            if config.protocol == Protocol.HTTPS:
                config.port = 8443
            elif config.protocol == Protocol.TCP:
                config.port = 8080
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_async()
    
    def execute(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute SQL query synchronously."""
        if self.config.protocol == Protocol.TCP:
            return self._execute_tcp_sync(sql, params)
        else:
            return self._execute_http_sync(sql, params)
    
    async def execute_async(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute SQL query asynchronously."""
        if self.config.protocol == Protocol.TCP:
            return await self._execute_tcp_async(sql, params)
        else:
            return await self._execute_http_async(sql, params)
    
    def _execute_http_sync(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute HTTP request synchronously."""
        url = f"{self.config.protocol.value}://{self.config.host}:{self.config.port}/"
        data = {"sql": sql, "params": params or []}
        
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            auth = base64.b64encode(f":{self.config.api_key}".encode()).decode()
            headers["Authorization"] = f"Basic {auth}"
        
        try:
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=self.config.timeout,
                verify=self.config.ssl_verify
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    async def _execute_http_async(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute HTTP request asynchronously."""
        if not self.session:
            connector = aiohttp.TCPConnector(limit=self.config.connection_pool_size)
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        url = f"{self.config.protocol.value}://{self.config.host}:{self.config.port}/"
        data = {"sql": sql, "params": params or []}
        
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            auth = base64.b64encode(f":{self.config.api_key}".encode()).decode()
            headers["Authorization"] = f"Basic {auth}"
        
        ssl_context = None
        if self.config.protocol == Protocol.HTTPS and not self.config.ssl_verify:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            async with self.session.post(url, json=data, headers=headers, ssl=ssl_context) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    return {"error": f"HTTP {response.status}: {text}"}
                    
        except aiohttp.ClientError as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def _execute_tcp_sync(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute TCP request synchronously."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.config.timeout)
        
        try:
            sock.connect((self.config.host, self.config.port))
            
            # Authenticate if API key is provided
            if self.config.api_key:
                sock.send(f"AUTH {self.config.api_key}\n".encode())
                response = sock.recv(1024).decode().strip()
                if not response.startswith("OK"):
                    return {"error": f"Authentication failed: {response}"}
            
            # Send SQL query
            sock.send(f"{sql}\n".encode())
            
            # Receive response
            response = ""
            while True:
                data = sock.recv(4096).decode()
                response += data
                if "\n" in response:
                    break
            
            return json.loads(response.strip())
            
        except Exception as e:
            return {"error": f"TCP request failed: {str(e)}"}
        finally:
            sock.close()
    
    async def _execute_tcp_async(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute TCP request asynchronously."""
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.config.host, self.config.port),
            timeout=self.config.timeout
        )
        
        try:
            # Authenticate if API key is provided
            if self.config.api_key:
                writer.write(f"AUTH {self.config.api_key}\n".encode())
                await writer.drain()
                response = await reader.readline()
                if not response.decode().strip().startswith("OK"):
                    return {"error": f"Authentication failed: {response.decode().strip()}"}
            
            # Send SQL query
            writer.write(f"{sql}\n".encode())
            await writer.drain()
            
            # Receive response
            response = await reader.readline()
            return json.loads(response.decode().strip())
            
        except Exception as e:
            return {"error": f"TCP request failed: {str(e)}"}
        finally:
            writer.close()
            await writer.wait_closed()
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        if self.config.protocol == Protocol.TCP:
            return {"error": "Server info not available via TCP protocol"}
        
        url = f"{self.config.protocol.value}://{self.config.host}:{self.config.port}/"
        
        try:
            response = requests.get(url, timeout=self.config.timeout, verify=self.config.ssl_verify)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    async def get_server_info_async(self) -> Dict[str, Any]:
        """Get server information asynchronously."""
        if self.config.protocol == Protocol.TCP:
            return {"error": "Server info not available via TCP protocol"}
        
        if not self.session:
            connector = aiohttp.TCPConnector(limit=self.config.connection_pool_size)
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        url = f"{self.config.protocol.value}://{self.config.host}:{self.config.port}/"
        
        ssl_context = None
        if self.config.protocol == Protocol.HTTPS and not self.config.ssl_verify:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            async with self.session.get(url, ssl=ssl_context) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    return {"error": f"HTTP {response.status}: {text}"}
        except aiohttp.ClientError as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def transaction(self, statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple SQL statements in a transaction."""
        results = []
        for stmt in statements:
            sql = stmt["sql"]
            params = stmt.get("params", [])
            result = self.execute(sql, params)
            if "error" in result:
                raise Exception(f"Transaction failed: {result['error']}")
            results.append(result)
        return results
    
    async def transaction_async(self, statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple SQL statements in a transaction asynchronously."""
        results = []
        for stmt in statements:
            sql = stmt["sql"]
            params = stmt.get("params", [])
            result = await self.execute_async(sql, params)
            if "error" in result:
                raise Exception(f"Transaction failed: {result['error']}")
            results.append(result)
        return results
    
    def close(self):
        """Close the client."""
        if self.session:
            self.session.close()
    
    async def close_async(self):
        """Close the client asynchronously."""
        if self.session:
            await self.session.close()


# Factory functions for easy client creation
def create_client(
    protocol: Union[str, Protocol] = "http",
    host: str = "localhost",
    port: int = 8000,
    api_key: Optional[str] = None,
    **kwargs
) -> MatsushibaDBClient:
    """Create a MatsushibaDB client."""
    if isinstance(protocol, str):
        protocol = Protocol(protocol)
    
    config = ClientConfig(
        protocol=protocol,
        host=host,
        port=port,
        api_key=api_key,
        **kwargs
    )
    
    return MatsushibaDBClient(config)


def create_http_client(host: str = "localhost", port: int = 8000, api_key: Optional[str] = None, **kwargs) -> MatsushibaDBClient:
    """Create an HTTP client."""
    return create_client(Protocol.HTTP, host, port, api_key, **kwargs)


def create_https_client(host: str = "localhost", port: int = 8443, api_key: Optional[str] = None, **kwargs) -> MatsushibaDBClient:
    """Create an HTTPS client."""
    return create_client(Protocol.HTTPS, host, port, api_key, **kwargs)


def create_tcp_client(host: str = "localhost", port: int = 8080, api_key: Optional[str] = None, **kwargs) -> MatsushibaDBClient:
    """Create a TCP client."""
    return create_client(Protocol.TCP, host, port, api_key, **kwargs)


# CLI interface
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="MatsushibaDB Python Client")
    parser.add_argument("protocol", choices=["http", "https", "tcp"], help="Protocol to use")
    parser.add_argument("host", help="Server host")
    parser.add_argument("port", type=int, help="Server port")
    parser.add_argument("api_key", help="API key")
    parser.add_argument("sql", help="SQL query")
    parser.add_argument("params", nargs="*", help="Query parameters")
    parser.add_argument("--async", dest="use_async", action="store_true", help="Use async client")
    
    args = parser.parse_args()
    
    client = create_client(args.protocol, args.host, args.port, args.api_key)
    
    try:
        if args.use_async:
            result = asyncio.run(client.execute_async(args.sql, args.params))
        else:
            result = client.execute(args.sql, args.params)
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()
