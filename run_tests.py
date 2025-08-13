"""
Quick test runner for Josh's Day 5 tasks
Run with: python run_tests.py
"""
import subprocess
import sys
import time

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ SUCCESS")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ FAILED")
            if result.stderr:
                print(result.stderr)
            if result.stdout:
                print(result.stdout)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all tests and diagnostics"""
    print("=" * 60)
    print("🚀 COGNITIVE COMPANION AGENT - TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("python -m pytest tests/test_basic.py -v", "Running Unit Tests"),
        ("python diagnose_recall.py", "Running Recall Diagnostic"),
        ("python eval.py", "Running Full Evaluation")
    ]
    
    results = []
    for cmd, desc in tests:
        success = run_command(cmd, desc)
        results.append((desc, success))
        time.sleep(1)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    for desc, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {desc}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your code is solid.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
