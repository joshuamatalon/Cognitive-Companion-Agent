#!/usr/bin/env python3
"""
Validation script to check if all improvements are properly implemented.
"""

import sys
from pathlib import Path
import importlib.util
from typing import List, Tuple

def check_module(module_name: str) -> Tuple[bool, str]:
    """Check if a Python module can be imported."""
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return True, "OK"
        except Exception as e:
            return False, f"Import error: {str(e)[:50]}"
    return False, "Module not found"

def validate_implementation():
    """Validate all implementation components."""
    print("=" * 60)
    print("COGNITIVE COMPANION - IMPLEMENTATION VALIDATION")
    print("=" * 60)
    
    results = []
    
    # Check core files exist
    print("\n📁 Checking Core Files:")
    core_files = [
        ("app.py", "Main application"),
        ("config.py", "Configuration"),
        ("vec_memory.py", "Vector memory"),
        ("hybrid_rag.py", "Hybrid RAG system"),
        ("production_search.py", "Production search"),
        ("requirements.txt", "Dependencies")
    ]
    
    for filepath, description in core_files:
        exists = Path(filepath).exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {description:<30} ({filepath})")
        results.append((description, exists))
    
    # Check security implementation
    print("\n🔒 Checking Security Implementation:")
    security_files = [
        ("secure_config.py", "Secure configuration"),
        ("setup_security.py", "Security setup"),
        ("rate_limiter.py", "Rate limiting"),
        ("sanitizer.py", "Input sanitization")
    ]
    
    for filepath, description in security_files:
        exists = Path(filepath).exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {description:<30} ({filepath})")
        results.append((description, exists))
    
    # Check performance modules
    print("\n⚡ Checking Performance Modules:")
    perf_files = [
        ("async_memory.py", "Async operations"),
        ("connection_pool.py", "Connection pooling"),
        ("improved_chunking.py", "Smart chunking")
    ]
    
    for filepath, description in perf_files:
        exists = Path(filepath).exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {description:<30} ({filepath})")
        results.append((description, exists))
    
    # Check analytics
    print("\n📊 Checking Analytics:")
    analytics_files = [
        ("analytics.py", "Analytics dashboard"),
        ("data/", "Data directory")
    ]
    
    for filepath, description in analytics_files:
        exists = Path(filepath).exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {description:<30} ({filepath})")
        results.append((description, exists))
    
    # Check testing infrastructure
    print("\n🧪 Checking Testing Infrastructure:")
    test_files = [
        ("tests/", "Tests directory"),
        ("tests/conftest.py", "Test configuration"),
        ("tests/test_memory_backend.py", "Backend tests")
    ]
    
    for filepath, description in test_files:
        exists = Path(filepath).exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {description:<30} ({filepath})")
        results.append((description, exists))
    
    # Check Python modules can be imported
    print("\n🐍 Checking Module Imports:")
    modules = [
        "streamlit",
        "openai",
        "pinecone",
        "langchain_openai",
        "pandas",
        "cryptography",
        "aiohttp",
        "pytest"
    ]
    
    for module in modules:
        success, message = check_module(module)
        status = "✅" if success else "❌"
        print(f"  {status} {module:<30} ({message})")
        results.append((f"Module: {module}", success))
    
    # Check configuration
    print("\n⚙️ Checking Configuration:")
    
    # Check if .env exists
    env_exists = Path(".env").exists()
    status = "✅" if env_exists else "⚠️"
    print(f"  {status} .env file {'exists' if env_exists else 'missing (using .env.example)'}")
    
    # Check if secure config exists
    secure_exists = Path(".secure_config").exists()
    status = "✅" if secure_exists else "ℹ️"
    print(f"  {status} Secure config {'configured' if secure_exists else 'not configured (run setup_security.py)'}")
    
    # Try to validate configuration
    try:
        from config import config
        if config.is_valid():
            print(f"  ✅ Configuration valid")
        else:
            print(f"  ❌ Configuration invalid: {', '.join(config.errors)}")
            results.append(("Configuration", False))
    except Exception as e:
        print(f"  ❌ Configuration error: {str(e)[:50]}")
        results.append(("Configuration", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n✅ Passed: {passed}/{total} ({success_rate:.1f}%)")
    
    if passed < total:
        print(f"❌ Failed: {total - passed}/{total}")
        print("\nFailed items:")
        for name, success in results:
            if not success:
                print(f"  • {name}")
    
    # Recommendations
    print("\n📝 Recommendations:")
    
    if not env_exists and not secure_exists:
        print("1. Copy .env.example to .env and add your API keys")
        print("   OR run 'python setup_security.py' for encrypted configuration")
    
    if not Path("tests/").exists():
        print("2. Tests directory missing - testing infrastructure incomplete")
    
    missing_modules = [m for m in ["streamlit", "openai", "pinecone"] if not check_module(m)[0]]
    if missing_modules:
        print(f"3. Install missing modules: pip install {' '.join(missing_modules)}")
    
    if success_rate < 80:
        print("4. Run 'python implement_improvements.py' to complete setup")
    
    print("\n" + "=" * 60)
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(validate_implementation())
