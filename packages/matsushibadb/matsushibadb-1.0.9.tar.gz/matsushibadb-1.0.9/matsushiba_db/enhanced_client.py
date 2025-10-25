"""
MatsushibaDB - Enhanced Python Client Library
Local database support, caching, async/await, and flexible configuration

@author MatsushibaDB Team
@version 2.0.0
"""

import asyncio
import os
import json
import sqlite3
import hashlib
import secrets
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging

# Internal SQLite engine (completely hidden from users)
try:
    import sqlite3 as sqlite3_module
except ImportError:
    sqlite3_module = None
    logging.warning('Database engine not available. Local database features disabled.')

class MatsushibaDBInternal:
    """Internal SQLite abstraction layer with encryption and custom format"""
    
    def __init__(self):
        self.encryption_key = None
        self.custom_format = True
        self.file_extension = '.msdb'
        self._internal_db = None
        self._internal_path = None

    def generate_encryption_key(self) -> str:
        """Generate a secure encryption key"""
        return secrets.token_hex(32)

    def convert_to_internal_format(self, user_path: str) -> str:
        """Convert user path to internal format"""
        if user_path.endswith(self.file_extension):
            return user_path[:-len(self.file_extension)] + '.db'
        return user_path + '.db'

    async def initialize_internal_database(self, database_path: str, options: Dict = None) -> sqlite3.Connection:
        """Initialize internal SQLite database with encryption"""
        if not sqlite3_module:
            raise RuntimeError('Database engine not available. Install database engine package for local database support.')

        options = options or {}
        
        # Set encryption key
        self.encryption_key = options.get('encryptionKey', self.generate_encryption_key())
        
        # Convert path to internal format
        internal_path = self.convert_to_internal_format(database_path)
        self._internal_path = internal_path
        
        # Decrypt/create database file
        await self.prepare_database_file(internal_path, database_path)

        # Create connection
        self._internal_db = sqlite3.connect(internal_path)
        self._internal_db.row_factory = sqlite3.Row
        
        # Configure SQLite for performance
        self._internal_db.execute('PRAGMA journal_mode=WAL')
        self._internal_db.execute('PRAGMA synchronous=NORMAL')
        self._internal_db.execute('PRAGMA cache_size=10000')
        self._internal_db.execute('PRAGMA mmap_size=268435456')
        self._internal_db.execute('PRAGMA wal_autocheckpoint=1000')
        self._internal_db.execute('PRAGMA busy_timeout=30000')
        
        return self._internal_db

    async def prepare_database_file(self, internal_path: str, user_path: str):
        """Prepare database file with encryption"""
        try:
            # Determine the encrypted file path
            encrypted_path = user_path if user_path.endswith(self.file_extension) else user_path + self.file_extension

            if os.path.exists(encrypted_path):
                # Decrypt existing encrypted file
                await self.decrypt_database_file(encrypted_path, internal_path)
            elif os.path.exists(internal_path):
                # Internal file exists, encrypt it
                await self.encrypt_database_file(internal_path, encrypted_path)
                # Remove the unencrypted internal file
                try:
                    os.unlink(internal_path)
                except OSError:
                    pass
            else:
                # Create new encrypted file
                await self.create_new_encrypted_database(internal_path, encrypted_path)
        except Exception as error:
            logging.warning(f'File preparation warning: {error}')
            # If file preparation fails, create a new empty database
            encrypted_path = user_path if user_path.endswith(self.file_extension) else user_path + self.file_extension
            await self.create_new_encrypted_database(internal_path, encrypted_path)

    async def create_new_encrypted_database(self, internal_path: str, encrypted_path: str):
        """Create new encrypted database"""
        # Create empty SQLite database
        temp_db = sqlite3.connect(internal_path)
        temp_db.close()

        # Wait a moment for file to be written
        await asyncio.sleep(0.1)

        # Encrypt the database file
        await self.encrypt_database_file(internal_path, encrypted_path)

        # Remove the unencrypted internal file
        try:
            os.unlink(internal_path)
        except OSError:
            pass

    async def encrypt_database_file(self, source_path: str, dest_path: str):
        """Encrypt database file using AES-256-CBC"""
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64

        # Generate key from password
        password = self.encryption_key.encode()
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        fernet = Fernet(key)

        # Read and encrypt file
        with open(source_path, 'rb') as file:
            file_data = file.read()

        encrypted_data = fernet.encrypt(file_data)

        # Write encrypted file with custom header
        with open(dest_path, 'wb') as file:
            # Custom header to identify MatsushibaDB files
            header = b'MATSUSHIBA_DB_V2.0\x00'
            file.write(header)
            file.write(salt)
            file.write(encrypted_data)

    async def decrypt_database_file(self, encrypted_path: str, dest_path: str):
        """Decrypt database file"""
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64

        with open(encrypted_path, 'rb') as file:
            # Read custom header
            header = file.read(18)
            if not header.startswith(b'MATSUSHIBA_DB_V2.0'):
                raise ValueError('Invalid MatsushibaDB file format')

            # Read salt and encrypted data
            salt = file.read(16)
            encrypted_data = file.read()

        # Generate key from password
        password = self.encryption_key.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        fernet = Fernet(key)

        # Decrypt data
        decrypted_data = fernet.decrypt(encrypted_data)

        # Write decrypted file
        with open(dest_path, 'wb') as file:
            file.write(decrypted_data)

    def execute_internal(self, query: str, params: tuple = None) -> Dict:
        """Execute query on internal database"""
        if not self._internal_db:
            raise RuntimeError('Database not initialized')

        cursor = self._internal_db.execute(query, params or ())
        
        if query.strip().upper().startswith('SELECT'):
            rows = [dict(row) for row in cursor.fetchall()]
            return {'rows': rows, 'last_id': None}
        else:
            self._internal_db.commit()
            return {'rows': [], 'last_id': cursor.lastrowid}

    def close_internal(self):
        """Close internal database connection"""
        if self._internal_db:
            self._internal_db.close()
            self._internal_db = None


class MatsushibaDBClient:
    """
    Enhanced MatsushibaDB client with local database support, caching, and flexible configuration
    """
    
    def __init__(self, options: Dict = None):
        """
        Create a new MatsushibaDB client with enhanced features
        
        Args:
            options: Connection options
                - mode: 'local', 'remote', or 'hybrid'
                - protocol: 'http', 'https', or 'tcp' (for remote)
                - host: Server host (for remote)
                - port: Server port (for remote)
                - apiKey: API key for authentication
                - database: Local database file path
                - cache: Cache configuration
                - config: Flexible configuration options
        """
        options = options or {}
        
        self.mode = options.get('mode', 'remote')
        self.protocol = options.get('protocol', 'http')
        self.host = options.get('host', 'localhost')
        self.port = options.get('port')
        self.api_key = options.get('apiKey')
        self.database = options.get('database', './matsushiba.msdb')
        self.timeout = options.get('timeout', 30)
        self.ssl = options.get('ssl', {})
        
        # Cache configuration
        self.cache = {
            'enabled': options.get('cache', {}).get('enabled', True),
            'ttl': options.get('cache', {}).get('ttl', 300),  # 5 minutes default
            'max_size': options.get('cache', {}).get('maxSize', 1000),
            **options.get('cache', {})
        }
        
        # Flexible configuration
        self.config = {
            # Local database settings
            'local': {
                'encryption': options.get('config', {}).get('local', {}).get('encryption', True),
                'backup': options.get('config', {}).get('local', {}).get('backup', True),
                'performance': options.get('config', {}).get('local', {}).get('performance', True)
            },
            # Remote connection settings
            'remote': {
                'retries': options.get('config', {}).get('remote', {}).get('retries', 3),
                'timeout': options.get('config', {}).get('remote', {}).get('timeout', 30),
                'keepalive': options.get('config', {}).get('remote', {}).get('keepalive', True)
            },
            # Security settings
            'security': {
                'encryption': options.get('config', {}).get('security', {}).get('encryption', True),
                'authentication': options.get('config', {}).get('security', {}).get('authentication', True),
                'audit': options.get('config', {}).get('security', {}).get('audit', False)
            }
        }
        
        # Internal components
        self._internal = MatsushibaDBInternal()
        self._cache_store = {}
        self._cache_timestamps = {}
        self._initialized = False
        self._connection = None

    async def initialize(self):
        """Initialize the client connection"""
        if self._initialized:
            return

        if self.mode in ['local', 'hybrid']:
            await self._internal.initialize_internal_database(
                self.database, 
                {'encryptionKey': self.config['security']['encryption']}
            )

        if self.mode in ['remote', 'hybrid']:
            # Initialize remote connection
            await self._initialize_remote_connection()

        self._initialized = True

    async def _initialize_remote_connection(self):
        """Initialize remote connection"""
        import aiohttp
        
        connector = aiohttp.TCPConnector(ssl=self.ssl.get('enabled', False))
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        self._connection = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
        )

    async def execute(self, query: str, params: tuple = None) -> Dict:
        """
        Execute SQL query with caching support
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result with rows and last_id
        """
        if not self._initialized:
            await self.initialize()

        # Check cache first
        cache_key = f"{query}:{str(params)}"
        if self.cache['enabled'] and cache_key in self._cache_store:
            if self._is_cache_valid(cache_key):
                return self._cache_store[cache_key]

        # Execute query based on mode
        if self.mode == 'local':
            result = self._internal.execute_internal(query, params)
        elif self.mode == 'remote':
            result = await self._execute_remote(query, params)
        elif self.mode == 'hybrid':
            # Try local first, fallback to remote
            try:
                result = self._internal.execute_internal(query, params)
            except Exception:
                result = await self._execute_remote(query, params)

        # Cache result
        if self.cache['enabled']:
            self._cache_store[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.now()
            
            # Cleanup old cache entries
            self._cleanup_cache()

        return result

    async def _execute_remote(self, query: str, params: tuple = None) -> Dict:
        """Execute query on remote server"""
        if not self._connection:
            raise RuntimeError('Remote connection not initialized')

        url = f"{self.protocol}://{self.host}:{self.port}/api/query"
        data = {'query': query, 'params': params or []}

        async with self._connection.post(url, json=data) as response:
            if response.status != 200:
                raise RuntimeError(f'Remote query failed: {response.status}')
            
            result = await response.json()
            return result

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        age = datetime.now() - self._cache_timestamps[cache_key]
        return age.total_seconds() < self.cache['ttl']

    def _cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, timestamp in self._cache_timestamps.items():
            age = current_time - timestamp
            if age.total_seconds() > self.cache['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._cache_store.pop(key, None)
            self._cache_timestamps.pop(key, None)

    def clear_cache(self):
        """Clear all cached data"""
        self._cache_store.clear()
        self._cache_timestamps.clear()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'size': len(self._cache_store),
            'max_size': self.cache['max_size'],
            'ttl': self.cache['ttl'],
            'enabled': self.cache['enabled']
        }

    async def transaction(self):
        """Context manager for database transactions"""
        return MatsushibaDBTransaction(self)

    async def begin_transaction(self):
        """Begin a new transaction"""
        await self.execute('BEGIN TRANSACTION')

    async def commit(self):
        """Commit the current transaction"""
        await self.execute('COMMIT')

    async def rollback(self):
        """Rollback the current transaction"""
        await self.execute('ROLLBACK')

    async def close(self):
        """Close the client connection"""
        if self._connection:
            await self._connection.close()
        
        if self._internal:
            self._internal.close_internal()
        
        self._initialized = False

    def get_status(self) -> Dict:
        """Get client status"""
        return {
            'initialized': self._initialized,
            'mode': self.mode,
            'cache_stats': self.get_cache_stats(),
            'database': self.database
        }

    def get_connection_info(self) -> Dict:
        """Get connection information"""
        return {
            'mode': self.mode,
            'protocol': self.protocol,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'timeout': self.timeout
        }

    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            await self.execute('SELECT 1')
            return True
        except Exception:
            return False


class MatsushibaDBTransaction:
    """Transaction context manager"""
    
    def __init__(self, client: MatsushibaDBClient):
        self.client = client
        self.active = False

    async def __aenter__(self):
        await self.client.begin_transaction()
        self.active = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.active:
            if exc_type is not None:
                await self.client.rollback()
            else:
                await self.client.commit()
        self.active = False

    async def execute(self, query: str, params: tuple = None) -> Dict:
        """Execute query within transaction"""
        return await self.client.execute(query, params)


# Export main classes
__all__ = ['MatsushibaDBClient', 'MatsushibaDBTransaction', 'MatsushibaDBInternal']
