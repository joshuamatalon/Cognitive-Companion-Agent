"""
Tune the alpha parameter for optimal hybrid search performance.
"""

import time
import json
from pathlib import Path
from search_enhancements import hybrid_search
from rag_chain import answer


def test_alpha_value(alpha: float):
    """Test a specific alpha value against eval_seed queries."""
    
    # Load test cases
    seed_path = Path("eval_seed.jsonl")
    cases = [
        json.loads(line)
        for line in seed_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    
    recall_count = 0
    answer_count = 0
    
    for case in cases:
        # Use hybrid search with specific alpha
        results = hybrid_search(case["q"], k=5, alpha=alpha)
        
        # Check recall
        if results:
            blob = " ".join([r[1] for r in results]).lower()
            recall_ok = all(x.lower() in blob for x in case["expect"])
            if recall_ok:
                recall_count += 1
        
        # Check answer (using the answer function)
        resp, _ = answer(case["q"], k=5)
        answer_ok = all(x.lower() in resp.lower() for x in case["expect"])
        if answer_ok:
            answer_count += 1
    
    recall_rate = recall_count / len(cases)
    answer_rate = answer_count / len(cases)
    
    return recall_rate, answer_rate


def main():
    """Test different alpha values to find the optimal setting."""
    
    print("Testing different alpha values for hybrid search...")
    print("=" * 60)
    
    alpha_values = [0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]
    best_alpha = 0.7
    best_recall = 0
    
    for alpha in alpha_values:
        print(f"\nTesting alpha = {alpha} (Vector: {alpha*100:.0f}%, Keyword: {(1-alpha)*100:.0f}%)")
        
        try:
            recall_rate, answer_rate = test_alpha_value(alpha)
            print(f"  Recall: {recall_rate:.1%}")
            print(f"  Answer: {answer_rate:.1%}")
            
            if recall_rate > best_recall:
                best_recall = recall_rate
                best_alpha = alpha
                
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"Best alpha value: {best_alpha}")
    print(f"Best recall rate: {best_recall:.1%}")
    
    # Update config with best alpha
    print(f"\nRecommendation: Use alpha={best_alpha} for optimal performance")
    
    return best_alpha


if __name__ == "__main__":
    main()