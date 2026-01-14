"""
Column-level encryption system
⭐ Creative standout feature
"""

import os
import base64
from typing import Union, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from ..core.exceptions import EncryptionError

class ColumnEncryptor:
    """Encrypt/decrypt values for specific columns"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize encryptor with master key
        
        Args:
            master_key: 32-byte master key. If None, reads from env.
        """
        if master_key is None:
            master_key = self._get_master_key_from_env()
        
        if len(master_key) != 32:
            raise EncryptionError("Master key must be 32 bytes (256 bits)")
        
        self.master_key = master_key
        self.column_keys = {}  # column_id -> derived_key
    
    def _get_master_key_from_env(self) -> bytes:
        """Get master key from environment variable"""
        key_hex = os.getenv('MALDB_MASTER_KEY')
        if not key_hex:
            # Generate a default key for development
            import secrets
            key_hex = secrets.token_hex(32)
            print(f"Warning: Using generated master key. For production, set MALDB_MASTER_KEY")
            print(f"Generated key: {key_hex}")
        
        try:
            return bytes.fromhex(key_hex)
        except ValueError:
            raise EncryptionError("Master key must be valid hex string")
    
    def get_column_key(self, column_id: str, salt: bytes = None) -> bytes:
        """
        Derive column-specific key from master key
        
        Args:
            column_id: Unique identifier for column (table.column)
            salt: Optional salt (generated if not provided)
            
        Returns:
            Derived 32-byte key for this column
        """
        if column_id in self.column_keys:
            return self.column_keys[column_id]
        
        if salt is None:
            # Generate salt from column_id
            salt = column_id.encode()[:16].ljust(16, b'\0')
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(self.master_key)
        self.column_keys[column_id] = key
        return key
    
    def encrypt_value(self, column_id: str, plaintext: str) -> str:
        """
        Encrypt a value for a specific column
        
        Args:
            column_id: Column identifier
            plaintext: Value to encrypt
            
        Returns:
            Base64-encoded ciphertext with nonce
        """
        if plaintext is None:
            return None
        
        key = self.get_column_key(column_id)
        aesgcm = AESGCM(key)
        
        # Generate random nonce (96 bits for AES-GCM)
        nonce = os.urandom(12)
        
        # Encrypt
        ciphertext = aesgcm.encrypt(
            nonce=nonce,
            data=plaintext.encode('utf-8'),
            associated_data=column_id.encode('utf-8')
        )
        
        # Combine nonce + ciphertext
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode('ascii')
    
    def decrypt_value(self, column_id: str, encrypted: str) -> str:
        """
        Decrypt a value for a specific column
        
        Args:
            column_id: Column identifier
            encrypted: Base64-encoded ciphertext
            
        Returns:
            Decrypted plaintext string
        """
        if encrypted is None:
            return None
        
        try:
            key = self.get_column_key(column_id)
            aesgcm = AESGCM(key)
            
            # Decode from base64
            combined = base64.b64decode(encrypted)
            
            # Extract nonce (first 12 bytes) and ciphertext
            nonce = combined[:12]
            ciphertext = combined[12:]
            
            # Decrypt
            plaintext = aesgcm.decrypt(
                nonce=nonce,
                data=ciphertext,
                associated_data=column_id.encode('utf-8')
            )
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")