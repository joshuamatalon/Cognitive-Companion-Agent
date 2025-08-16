"""
Secure configuration management with encryption for API keys.
Provides encrypted storage and runtime decryption of sensitive data.
"""
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
from pathlib import Path
import json
from typing import Optional, Dict, Any
import getpass

class SecureConfig:
    """Encrypted configuration management with runtime decryption."""
    
    def __init__(self, master_key: Optional[str] = None):
        self.config_file = Path(".secure_config")
        self.salt_file = Path(".salt")
        self._cipher = None
        self._config = {}
        self._master_key = master_key or self._get_master_key()
        self._initialize_cipher()
    
    def _get_master_key(self) -> str:
        """Get master key from environment or prompt."""
        # Try environment variable first
        key = os.getenv("CCA_MASTER_KEY")
        if key:
            return key
        
        # Try key file (for development)
        key_file = Path(".master_key")
        if key_file.exists():
            return key_file.read_text().strip()
        
        # Prompt user (fallback)
        return getpass.getpass("Enter master key: ")
    
    def _initialize_cipher(self):
        """Initialize Fernet cipher with derived key."""
        # Generate or load salt
        if self.salt_file.exists():
            salt = self.salt_file.read_bytes()
        else:
            salt = os.urandom(16)
            self.salt_file.write_bytes(salt)
            if os.name != 'nt':  # Unix/Linux
                self.salt_file.chmod(0o600)  # Restrict permissions
        
        # Derive encryption key from master key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._master_key.encode()))
        self._cipher = Fernet(key)
    
    def set_secret(self, key: str, value: str):
        """Encrypt and store a secret."""
        encrypted_value = self._cipher.encrypt(value.encode())
        
        # Load existing config
        if self.config_file.exists():
            config = json.loads(self.config_file.read_text())
        else:
            config = {}
        
        # Update with encrypted value
        config[key] = base64.b64encode(encrypted_value).decode()
        
        # Save config
        self.config_file.write_text(json.dumps(config, indent=2))
        if os.name != 'nt':  # Unix/Linux
            self.config_file.chmod(0o600)  # Restrict permissions
    
    def get_secret(self, key: str) -> Optional[str]:
        """Decrypt and retrieve a secret."""
        if not self.config_file.exists():
            return None
        
        try:
            config = json.loads(self.config_file.read_text())
            if key not in config:
                return None
            
            encrypted_value = base64.b64decode(config[key])
            decrypted = self._cipher.decrypt(encrypted_value)
            return decrypted.decode()
        except Exception as e:
            print(f"Failed to decrypt {key}: {e}")
            return None
    
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        """Get decrypted OpenAI API key."""
        return self.get_secret("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    @property
    def PINECONE_API_KEY(self) -> Optional[str]:
        """Get decrypted Pinecone API key."""
        return self.get_secret("PINECONE_API_KEY") or os.getenv("PINECONE_API_KEY")
    
    def validate(self) -> bool:
        """Validate all required secrets are available."""
        required = ["OPENAI_API_KEY", "PINECONE_API_KEY"]
        for key in required:
            if not getattr(self, key):
                print(f"Missing required secret: {key}")
                return False
        return True
    
    def setup_wizard(self):
        """Interactive setup for first-time configuration."""
        print("=" * 60)
        print("SECURE CONFIGURATION SETUP")
        print("=" * 60)
        
        # Get API keys
        openai_key = getpass.getpass("Enter OpenAI API Key (sk-...): ")
        pinecone_key = getpass.getpass("Enter Pinecone API Key (pcsk_...): ")
        
        # Validate format
        if not openai_key.startswith(("sk-", "org-")):
            print("Warning: OpenAI key format looks incorrect")
        
        if not pinecone_key.startswith("pcsk_"):
            print("Warning: Pinecone key format looks incorrect")
        
        # Store encrypted
        self.set_secret("OPENAI_API_KEY", openai_key)
        self.set_secret("PINECONE_API_KEY", pinecone_key)
        
        print("\n✅ Secrets encrypted and stored")
        print("Add .secure_config and .salt to .gitignore!")
        
        # Test decryption
        if self.validate():
            print("✅ Configuration validated successfully")
        else:
            print("❌ Configuration validation failed")
