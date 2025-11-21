"""
Test LLM availability and intent classification with LLM fallback.
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator.llm_connector import get_llm_connector, generate_response
from orchestrator.orchestrator import classify_intent, _classify_intent_with_llm

def test_llm_connector():
    """Test basic LLM connector functionality."""
    print("\n" + "="*80)
    print("LLM CONNECTOR TEST")
    print("="*80)
    
    try:
        connector = get_llm_connector()
        print(f"✅ LLM Connector initialized: {type(connector).__name__}")
        
        # Test generate_response
        print("\n" + "-"*80)
        print("Testing generate_response()...")
        print("-"*80)
        
        response = generate_response(
            prompt="Say 'Hello' in one word",
            context=[]
        )
        print(f"✅ LLM Response: {response[:100]}")
        
    except Exception as e:
        print(f"❌ LLM Connector failed: {e}")
        import traceback
        traceback.print_exc()


def test_llm_intent_classification():
    """Test LLM-based intent classification."""
    print("\n" + "="*80)
    print("LLM INTENT CLASSIFICATION TEST")
    print("="*80)
    
    test_queries = [
        "i am going to a birthday party tomorrow",
        "what is the weather today?",
        "tell me a joke",
        "I need perfumes for a gift"
    ]
    
    for query in test_queries:
        print(f"\n" + "-"*80)
        print(f"Query: '{query}'")
        print("-"*80)
        
        try:
            result = _classify_intent_with_llm(query)
            
            if result:
                print(f"✅ LLM Classification:")
                print(f"  Category: {result['category']}")
                print(f"  Confidence: {result['confidence']:.3f}")
                print(f"  Reasoning: {result.get('reasoning', 'N/A')}")
                print(f"  Strategy: {result['strategy']}")
            else:
                print(f"❌ LLM classification returned None")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


def test_hybrid_classification():
    """Test full hybrid classification with LLM fallback."""
    print("\n" + "="*80)
    print("HYBRID CLASSIFICATION TEST (with LLM fallback)")
    print("="*80)
    
    # Edge case that should trigger LLM
    query = "i am going to a birthday party tomorrow"
    
    print(f"\nQuery: '{query}'")
    print("\nExpected behavior:")
    print("  - Fuzzy match to LOGIN (confidence ~0.74)")
    print("  - Confidence < 0.85 for fuzzy match")
    print("  - Should trigger LLM validation (Option C)")
    
    print("\n" + "-"*80)
    print("Testing with use_hybrid=True:")
    print("-"*80)
    
    try:
        result = classify_intent(query, use_hybrid=True)
        
        if result:
            print(f"\nResult:")
            print(f"  Category: {result.category.value}")
            print(f"  Confidence: {result.confidence:.3f}")
            print(f"  Strategy: {result.metadata.get('strategy', 'N/A')}")
            print(f"  Needs Clarification: {result.metadata.get('needs_clarification', False)}")
            
            if 'reasoning' in result.metadata:
                print(f"  LLM Reasoning: {result.metadata['reasoning']}")
                print(f"  ✅ LLM was used for validation")
            
            if 'keyword_match' in result.metadata:
                print(f"  Original Keyword Match: {result.metadata['keyword_match']}")
                print(f"  Keyword Confidence: {result.metadata['keyword_confidence']:.3f}")
            
            if 'matched_keywords' in result.metadata:
                print(f"  Matched Keywords: {result.metadata['matched_keywords']}")
                print(f"  Match Type: {result.metadata.get('best_match_type', 'N/A')}")
            
            # Check if LLM improved the result
            if result.metadata.get('strategy') in ['llm_fallback', 'hybrid_llm_validation']:
                print(f"\n  ✅✅ SUCCESS: LLM fallback was triggered and used")
            else:
                print(f"\n  ⚠️ LLM fallback was not triggered")
        
        else:
            print(f"❌ Classification returned None")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING LLM AVAILABILITY AND FUNCTIONALITY")
    print("="*80)
    
    # Test 1: Basic LLM connector
    test_llm_connector()
    
    # Test 2: LLM intent classification function
    test_llm_intent_classification()
    
    # Test 3: Hybrid classification with LLM fallback
    test_hybrid_classification()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETE")
    print("="*80)
