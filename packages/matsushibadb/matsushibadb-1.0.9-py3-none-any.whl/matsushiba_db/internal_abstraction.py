"""
MatsushibaDB - Internal SQLite Abstraction Layer
Transparent SQLite handling with file encryption and custom format

@author MatsushibaDB Team
@version 2.0.0
"""

import os
import sqlite3
import secrets
import hashlib
import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime

# Internal SQLite engine (completely hidden from users)
try:
    import sqlite3 as sqlite3_module
except ImportError:
    sqlite3_module = None
    logging.warning('Database engine not available. Local database features disabled.')


class MatsushibaDBInternal:
    """
    Internal SQLite abstraction layer with encryption and custom format
    Completely hides SQLite implementation from users
    """
    
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
        """
        Initialize internal SQLite database with encryption
        Users never see SQLite - they only work with MatsushibaDB
        """
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
        
        # Configure SQLite for performance (hidden from users)
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
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            import base64
        except ImportError:
            # Fallback to basic encryption if cryptography not available
            await self._basic_encrypt_file(source_path, dest_path)
            return

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
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            import base64
        except ImportError:
            # Fallback to basic decryption if cryptography not available
            await self._basic_decrypt_file(encrypted_path, dest_path)
            return

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

    async def _basic_encrypt_file(self, source_path: str, dest_path: str):
        """Basic file encryption fallback"""
        import base64
        
        with open(source_path, 'rb') as file:
            file_data = file.read()
        
        # Simple XOR encryption with key
        key = self.encryption_key.encode()
        encrypted_data = bytearray()
        for i, byte in enumerate(file_data):
            encrypted_data.append(byte ^ key[i % len(key)])
        
        # Write with custom header
        with open(dest_path, 'wb') as file:
            header = b'MATSUSHIBA_DB_V2.0\x00'
            file.write(header)
            file.write(base64.b64encode(bytes(encrypted_data)))

    async def _basic_decrypt_file(self, encrypted_path: str, dest_path: str):
        """Basic file decryption fallback"""
        import base64
        
        with open(encrypted_path, 'rb') as file:
            # Read custom header
            header = file.read(18)
            if not header.startswith(b'MATSUSHIBA_DB_V2.0'):
                raise ValueError('Invalid MatsushibaDB file format')
            
            encrypted_data = base64.b64decode(file.read())
        
        # Simple XOR decryption with key
        key = self.encryption_key.encode()
        decrypted_data = bytearray()
        for i, byte in enumerate(encrypted_data):
            decrypted_data.append(byte ^ key[i % len(key)])
        
        # Write decrypted file
        with open(dest_path, 'wb') as file:
            file.write(bytes(decrypted_data))

    def execute_internal(self, query: str, params: tuple = None) -> Dict:
        """
        Execute query on internal database
        Users never see this - they only use MatsushibaDB methods
        """
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

    def get_encryption_key(self) -> str:
        """Get current encryption key"""
        return self.encryption_key

    async def reencrypt_database(self, new_key: str):
        """Re-encrypt database with new key"""
        if not self._internal_path:
            raise RuntimeError('No database to re-encrypt')
        
        # Get current database path
        encrypted_path = self._internal_path.replace('.db', self.file_extension)
        
        # Decrypt with old key
        temp_path = self._internal_path + '.temp'
        await self.decrypt_database_file(encrypted_path, temp_path)
        
        # Update key
        old_key = self.encryption_key
        self.encryption_key = new_key
        
        # Encrypt with new key
        await self.encrypt_database_file(temp_path, encrypted_path)
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass

    def get_file_extension(self) -> str:
        """Get custom file extension"""
        return self.file_extension

    def is_custom_format(self) -> bool:
        """Check if using custom format"""
        return self.custom_format


# Export for use in other modules
__all__ = ['MatsushibaDBInternal']
