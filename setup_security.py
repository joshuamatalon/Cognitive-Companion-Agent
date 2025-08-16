#!/usr/bin/env python3
"""
Security setup wizard for Cognitive Companion Agent
Run this to configure encrypted API keys
"""

from secure_config import SecureConfig
from pathlib import Path

def main():
    print("COGNITIVE COMPANION SECURITY SETUP")
    print("=" * 40)
    
    # Check if already configured
    if Path(".secure_config").exists():
        response = input("Secure config exists. Reconfigure? (y/n): ")
        if response.lower() != 'y':
            print("Setup cancelled")
            return
    
    # Run setup wizard
    secure = SecureConfig()
    secure.setup_wizard()
    
    # Update .gitignore
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        additions = []
        
        if ".secure_config" not in content:
            additions.append(".secure_config")
        if ".salt" not in content:
            additions.append(".salt")
        if ".master_key" not in content:
            additions.append(".master_key")
        
        if additions:
            with open(gitignore, 'a') as f:
                f.write("\n# Secure configuration\n")
                for item in additions:
                    f.write(f"{item}\n")
            print(f"✅ Added {len(additions)} items to .gitignore")
    
    print("\n" + "=" * 40)
    print("SETUP COMPLETE!")
    print("\nFor production deployment:")
    print("1. Set CCA_MASTER_KEY environment variable")
    print("2. Copy .secure_config and .salt to server")
    print("3. Never commit these files to git")
    print("=" * 40)

if __name__ == "__main__":
    main()
