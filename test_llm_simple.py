"""
Simple test for LLM and hybrid classification (no emoji).
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator.orchestrator import classify_intent

def test_llm_hybrid():
    """Test hybrid classification with LLM fallback."""
    print("\n" + "="*80)
    print("HYBRID CLASSIFICATION TEST - Birthday Party Edge Case")
    print("="*80)
    
    query = "i am going to a birthday party tomorrow"
    
    print(f"\nQuery: '{query}'")
    print("\nWith use_hybrid=True (LLM fallback enabled):")
    print("-"*80)
    
    result = classify_intent(query, use_hybrid=True)
    
    if result:
        print(f"Category: {result.category.value}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Strategy: {result.metadata.get('strategy', 'N/A')}")
        print(f"Needs Clarification: {result.metadata.get('needs_clarification', False)}")
        
        if 'reasoning' in result.metadata:
            print(f"LLM Reasoning: {result.metadata['reasoning'][:150]}...")
            print(f"\n[SUCCESS] LLM was used for validation/classification")
        
        if 'matched_keywords' in result.metadata:
            print(f"Matched Keywords: {result.metadata['matched_keywords']}")
            print(f"Match Type: {result.metadata.get('best_match_type', 'N/A')}")
        
        if 'keyword_match' in result.metadata:
            print(f"Original Keyword Match: {result.metadata['keyword_match']}")
            print(f"Keyword Confidence: {result.metadata['keyword_confidence']:.3f}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    test_llm_hybrid()
