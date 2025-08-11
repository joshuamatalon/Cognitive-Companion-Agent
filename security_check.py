#!/usr/bin/env python3
"""
Security validation script for Cognitive Companion App
Checks for common security issues before deployment
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def check_api_keys() -> List[str]:
    """Check for exposed API keys in source files"""
    issues = []
    
    # Patterns to look for
    patterns = [
        (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI API Key'),
        (r'pcsk_[a-zA-Z0-9_]{20,}', 'Pinecone API Key'),
        (r'OPENAI_API_KEY\s*=\s*["\']?sk-', 'OpenAI API Key assignment'),
        (r'PINECONE_API_KEY\s*=\s*["\']?pcsk_', 'Pinecone API Key assignment'),
    ]
    
    # Files to check
    extensions = ['.py', '.ps1', '.bat', '.sh', '.md', '.txt', '.json', '.yml', '.yaml']
    
    for ext in extensions:
        for file_path in Path('.').rglob(f'*{ext}'):
            # Skip hidden files and directories
            if any(part.startswith('.') for part in file_path.parts[1:]):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                for pattern, desc in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(f"CRITICAL: {desc} found in {file_path}:{line_num}")
                        
            except Exception:
                continue
    
    return issues

def check_hardcoded_paths() -> List[str]:
    """Check for hardcoded paths with usernames"""
    issues = []
    
    patterns = [
        (r'C:\\Users\\[^\\]+', 'Windows user path'),
        (r'/home/[^/]+', 'Linux user path'),
        (r'/Users/[^/]+', 'macOS user path'),
    ]
    
    extensions = ['.py', '.ps1', '.bat', '.sh']
    
    for ext in extensions:
        for file_path in Path('.').rglob(f'*{ext}'):
            if any(part.startswith('.') for part in file_path.parts[1:]):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                for pattern, desc in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(f"WARNING: {desc} found in {file_path}:{line_num}: {match.group()}")
                        
            except Exception:
                continue
    
    return issues

def check_env_file() -> List[str]:
    """Check .env file for placeholder values"""
    issues = []
    
    env_file = Path('.env')
    if env_file.exists():
        try:
            content = env_file.read_text()
            
            if 'your-openai-api-key-here' in content:
                issues.append("OK: .env has placeholder OpenAI key (good)")
            elif 'sk-' in content:
                issues.append("CRITICAL: .env contains real OpenAI API key!")
                
            if 'your-pinecone-api-key-here' in content:
                issues.append("OK: .env has placeholder Pinecone key (good)")
            elif 'pcsk_' in content:
                issues.append("CRITICAL: .env contains real Pinecone API key!")
                
        except Exception as e:
            issues.append(f"❌ Could not read .env file: {e}")
    else:
        issues.append("WARNING: No .env file found")
    
    return issues

def check_gitignore() -> List[str]:
    """Check if sensitive files are properly ignored"""
    issues = []
    
    gitignore_file = Path('.gitignore')
    if gitignore_file.exists():
        try:
            content = gitignore_file.read_text()
            
            required_ignores = ['.env', '__pycache__', '*.pyc', '.venv', 'venv/']
            
            for item in required_ignores:
                if item not in content:
                    issues.append(f"WARNING: {item} not in .gitignore")
                else:
                    issues.append(f"OK: {item} properly ignored")
                    
        except Exception as e:
            issues.append(f"❌ Could not read .gitignore: {e}")
    else:
        issues.append("WARNING: No .gitignore file found")
    
    return issues

def main():
    """Run all security checks"""
    print("COGNITIVE COMPANION SECURITY CHECK")
    print("=" * 40)
    
    all_issues = []
    
    # Check for API keys
    print("\nChecking for exposed API keys...")
    api_issues = check_api_keys()
    all_issues.extend(api_issues)
    
    if api_issues:
        for issue in api_issues:
            print(f"  {issue}")
    else:
        print("  OK: No exposed API keys found")
    
    # Check for hardcoded paths
    print("\nChecking for hardcoded paths...")
    path_issues = check_hardcoded_paths()
    all_issues.extend(path_issues)
    
    if path_issues:
        for issue in path_issues:
            print(f"  {issue}")
    else:
        print("  OK: No hardcoded user paths found")
    
    # Check .env file
    print("\nChecking .env file...")
    env_issues = check_env_file()
    for issue in env_issues:
        print(f"  {issue}")
    
    # Check .gitignore
    print("\nChecking .gitignore...")
    git_issues = check_gitignore()
    for issue in git_issues:
        print(f"  {issue}")
    
    # Summary
    print("\n" + "=" * 40)
    critical_issues = [issue for issue in all_issues if 'CRITICAL' in issue]
    
    if critical_issues:
        print(f"CRITICAL: {len(critical_issues)} CRITICAL ISSUES FOUND!")
        print("NOT SAFE FOR DEPLOYMENT")
        return 1
    else:
        print("SECURITY CHECK PASSED")
        print("SAFE FOR DEPLOYMENT")
        return 0

if __name__ == "__main__":
    exit(main())