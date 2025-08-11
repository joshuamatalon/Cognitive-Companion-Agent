#!/usr/bin/env python3
"""Test script to debug reset_all functionality"""

import sys
import traceback
from vec_memory import reset_all, get_memory_stats, upsert_note

def test_reset():
    print("=== Testing Reset All Memory ===")
    
    try:
        # First, check current stats
        print("\n1. Getting current memory stats...")
        stats = get_memory_stats()
        print(f"Current stats: {stats}")
        
        # Add a test memory if none exist
        if stats.get("total_memories", 0) == 0:
            print("\n2. Adding a test memory first...")
            test_id = upsert_note("Test memory for reset", {"type": "test"})
            print(f"Added test memory: {test_id}")
            
            # Check stats again
            stats = get_memory_stats()
            print(f"Stats after adding test: {stats}")
        
        print(f"\n3. Attempting to reset {stats.get('total_memories', 0)} memories...")
        
        # Attempt reset
        reset_all()
        print("SUCCESS: Reset completed successfully!")
        
        # Check stats after reset
        print("\n4. Checking stats after reset...")
        final_stats = get_memory_stats()
        print(f"Final stats: {final_stats}")
        
        if final_stats.get("total_memories", -1) == 0:
            print("SUCCESS: Reset successful - all memories cleared!")
        else:
            print(f"WARNING: Reset may not have worked - still {final_stats.get('total_memories')} memories")
            
    except Exception as e:
        print(f"ERROR: Reset failed with error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_reset()
    sys.exit(0 if success else 1)