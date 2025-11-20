"""
Debug test to see what LLM is actually returning.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator.orchestrator import _classify_intent_with_llm

def test_llm_raw():
    """Test raw LLM classification output."""
    print("\n" + "="*80)
    print("LLM CLASSIFICATION DEBUG TEST")
    print("="*80)
    
    test_queries = [
        "i am going to a birthday party tomorrow",
        "show me perfumes",
        "what is the weather?",
        "hello"
    ]
    
    for query in test_queries:
        print(f"\n{'-'*80}")
        print(f"Query: '{query}'")
        print(f"{'-'*80}")
        
        result = _classify_intent_with_llm(query)
        
        if result:
            print(f"Category: {result['category']}")
            print(f"Confidence: {result['confidence']:.3f}")
            print(f"Strategy: {result['strategy']}")
            print(f"Reasoning (first 300 chars):")
            print(f"  {result['reasoning'][:300]}")
        else:
            print("Result: None")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    test_llm_raw()
