"""
Column-level encryption system with key persistence
⭐ Creative standout feature
"""

import os
import base64
import json
from typing import Union, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from ..core.exceptions import EncryptionError

class ColumnEncryptor:
    """Encrypt/decrypt values for specific columns"""
    
    def __init__(self, master_key: Optional[bytes] = None, key_file: str = "maldb_keys.json", silent: bool = False):
        """
        Initialize encryptor with master key
        
        Args:
            master_key: 32-byte master key. If None, reads from env or file.
            key_file: Path to key file for persistence
            silent: If True, don't print warnings
        """
        self.silent = silent
        self.key_file = key_file
        self.column_keys: dict = {}  # Initialize column_keys dictionary
        
        # Set master key
        if master_key:
            self.master_key = master_key
        else:
            self.master_key = self._get_or_create_master_key()
    
    def _get_or_create_master_key(self) -> bytes:
        """Get master key from environment, file, or generate new"""
        # Try environment variable first
        key_hex = os.getenv('MALDB_MASTER_KEY')
        
        # If not in env, try to load from file
        if not key_hex and os.path.exists(self.key_file):
            try:
                with open(self.key_file, 'r') as f:
                    key_data = json.load(f)
                    key_hex = key_data.get('master_key')
                    if not self.silent:
                        print(f"✅ Loaded master key from {self.key_file}")
            except:
                pass
        
        # If still no key, generate one
        if not key_hex:
            import secrets
            key_hex = secrets.token_hex(32)
            if not self.silent:
                print(f"🔑 Generated new master key. Saving to {self.key_file}")
            
            # Save to file for persistence
            try:
                os.makedirs(os.path.dirname(self.key_file) if os.path.dirname(self.key_file) else '.', exist_ok=True)
                with open(self.key_file, 'w') as f:
                    json.dump({
                        'master_key': key_hex,
                        'warning': 'Keep this key secure! Do not commit to version control.'
                    }, f, indent=2)
                if not self.silent:
                    print(f"✅ Master key saved to {self.key_file}")
            except Exception as e:
                if not self.silent:
                    print(f"⚠️  Could not save key to file: {e}")
                    print(f"   Using in-memory key for this session only.")
        
        try:
            return bytes.fromhex(key_hex)
        except ValueError:
            raise EncryptionError("Master key must be valid hex string")
    
    def _generate_key(self) -> bytes:
        """Generate a random encryption key - this is the missing method"""
        import secrets
        return secrets.token_bytes(32)
    
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
            return ""
        
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
        if encrypted is None or encrypted == "":
            return ""
        
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
            # If decryption fails, return placeholder
            if not self.silent:
                print(f"⚠️  Decryption failed for {column_id}: {e}")
            return "[ENCRYPTED]"
    
    def bulk_encrypt(self, column_id: str, values: list) -> list:
        """Encrypt multiple values for a column"""
        return [self.encrypt_value(column_id, str(v)) if v is not None else "" for v in values]
    
    def bulk_decrypt(self, column_id: str, encrypted_values: list) -> list:
        """Decrypt multiple values for a column"""
        return [self.decrypt_value(column_id, v) if v else "" for v in encrypted_values]