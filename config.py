"""
Secure configuration module for API keys and environment variables.
Validates and safely loads sensitive configuration.
"""
import os
import sys
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration with validation."""
    
    def __init__(self):
        self.errors = []
        
        # Load and validate API keys
        self.OPENAI_API_KEY = self._get_required_env("OPENAI_API_KEY")
        self.PINECONE_API_KEY = self._get_required_env("PINECONE_API_KEY")
        self.PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
        
        # Security checks
        self._validate_api_keys()
        
        # If there are errors, display them
        if self.errors:
            print("\n⚠️  Configuration Errors:")
            for error in self.errors:
                print(f"   • {error}")
            print("\n📝 Setup Instructions:")
            print("   1. Copy .env.example to .env")
            print("   2. Add your API keys to .env")
            print("   3. Never commit .env to version control\n")
    
    def _get_required_env(self, key: str) -> Optional[str]:
        """Get required environment variable with validation."""
        value = os.getenv(key)
        if not value:
            self.errors.append(f"Missing {key}")
        elif value == f"your-{key.lower().replace('_', '-')}-here":
            self.errors.append(f"{key} is still set to placeholder value")
        return value
    
    def _validate_api_keys(self):
        """Validate API key formats."""
        # Check OpenAI key format
        if self.OPENAI_API_KEY and not self.OPENAI_API_KEY.startswith(("sk-", "org-")):
            self.errors.append("OPENAI_API_KEY has invalid format")
        
        # Check Pinecone key format  
        if self.PINECONE_API_KEY and not self.PINECONE_API_KEY.startswith("pcsk_"):
            self.errors.append("PINECONE_API_KEY has invalid format")
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.errors) == 0
    
    def get_safe_display(self, key: str) -> str:
        """Get masked version of API key for display."""
        value = getattr(self, key, None)
        if not value:
            return "Not configured"
        if len(value) > 8:
            return f"{value[:4]}...{value[-4:]}"
        return "***"

# Create singleton instance
config = Config()

# Export for easy import
__all__ = ['config']