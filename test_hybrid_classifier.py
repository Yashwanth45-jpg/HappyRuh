"""
Comprehensive Test Suite for Hybrid Intent Classifier

Tests all advanced features:
- Simple vs hybrid classification
- Ambiguous query handling
- Multi-intent detection
- Context-aware classification
- Embedding matching
- Confidence calibration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intent_classifier import classify_intent, IntentCategory


def test_simple_queries():
    """Test fast keyword-based classification"""
    print("\n" + "=" * 80)
    print("TEST 1: SIMPLE QUERIES (Keyword-Only Mode)")
    print("=" * 80)
    
    test_cases = [
        ("hi", IntentCategory.GREETING),
        ("show my cart", IntentCategory.VIEW_CART),
        ("track my order", IntentCategory.TRACK_ORDER),
        ("bye", IntentCategory.GOODBYE),
    ]
    
    for query, expected in test_cases:
        result = classify_intent(query, use_hybrid=False)
        status = "✅" if result.category == expected else "❌"
        print(f"{status} '{query}'")
        print(f"   Expected: {expected.value}, Got: {result.category.value}")
        print(f"   Confidence: {result.confidence:.2f}, Time: {result.processing_time_ms:.2f}ms")


def test_hybrid_mode():
    """Test hybrid classification with embeddings"""
    print("\n" + "=" * 80)
    print("TEST 2: HYBRID MODE (Keyword + Embedding)")
    print("=" * 80)
    
    test_cases = [
        "I want to buy something nice for my wedding",
        "Can you help me find affordable products?",
        "What's good for a party?",
        "I'm looking for something luxurious",
    ]
    
    for query in test_cases:
        result = classify_intent(query, use_hybrid=True)
        print(f"\nQuery: '{query}'")
        print(f"  Category: {result.category.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Strategy: {result.metadata.get('strategy', 'unknown')}")
        print(f"  Entities: {result.entities}")
        print(f"  Time: {result.processing_time_ms:.2f}ms")


def test_ambiguous_queries():
    """Test ambiguity handling"""
    print("\n" + "=" * 80)
    print("TEST 3: AMBIGUOUS QUERIES")
    print("=" * 80)
    
    test_cases = [
        "show me products and add to cart",
        "I want to search but also compare",
        "find perfumes or attars under 500",
    ]
    
    for query in test_cases:
        result = classify_intent(query, use_hybrid=True)
        print(f"\nQuery: '{query}'")
        print(f"  Category: {result.category.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Needs Clarification: {result.metadata.get('needs_clarification', False)}")
        
        if result.metadata.get('clarification_message'):
            print(f"  Clarification: {result.metadata['clarification_message']}")


def test_entity_extraction():
    """Test entity extraction"""
    print("\n" + "=" * 80)
    print("TEST 4: ENTITY EXTRACTION")
    print("=" * 80)
    
    test_cases = [
        "show me perfumes under 500",
        "I want attars between 100 and 300",
        "find crystals for party",
        "recommend perfumes for men under 1000",
        "I need 2 bottles of fragrance for wedding",
    ]
    
    for query in test_cases:
        result = classify_intent(query, use_hybrid=False)
        print(f"\nQuery: '{query}'")
        print(f"  Entities: {result.entities}")


def test_context_awareness():
    """Test context-aware classification"""
    print("\n" + "=" * 80)
    print("TEST 5: CONTEXT-AWARE CLASSIFICATION")
    print("=" * 80)
    
    # Context: User just added items to cart
    context = {
        'cart_items': 3,
        'just_added_to_cart': True,
        'recent_action': 'added_to_cart'
    }
    
    query = "show me what I have"
    result = classify_intent(query, use_hybrid=True, context=context)
    
    print(f"Query: '{query}'")
    print(f"Context: User just added items to cart")
    print(f"  Category: {result.category.value}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  (Should prefer VIEW_CART due to context)")


def test_confidence_calibration():
    """Test confidence score distribution"""
    print("\n" + "=" * 80)
    print("TEST 6: CONFIDENCE CALIBRATION")
    print("=" * 80)
    
    test_cases = [
        ("hi", "Very simple, high confidence"),
        ("show my cart", "Exact phrase match, high confidence"),
        ("I want something nice", "Vague, medium confidence"),
        ("xyz abc def", "Nonsense, low confidence"),
    ]
    
    for query, description in test_cases:
        result = classify_intent(query, use_hybrid=False)
        print(f"\n'{query}' - {description}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Category: {result.category.value}")


def test_performance():
    """Test classification performance"""
    print("\n" + "=" * 80)
    print("TEST 7: PERFORMANCE BENCHMARKS")
    print("=" * 80)
    
    import time
    
    # Test keyword-only mode
    queries = ["show me perfumes"] * 100
    start = time.time()
    for q in queries:
        classify_intent(q, use_hybrid=False)
    keyword_time = (time.time() - start) * 1000 / 100
    
    print(f"Keyword-only mode: {keyword_time:.2f}ms average")
    
    # Test hybrid mode (if available)
    try:
        start = time.time()
        for q in queries[:10]:  # Smaller sample for hybrid
            classify_intent(q, use_hybrid=True)
        hybrid_time = (time.time() - start) * 1000 / 10
        print(f"Hybrid mode: {hybrid_time:.2f}ms average")
    except Exception as e:
        print(f"Hybrid mode unavailable: {e}")


def test_multi_intent_detection():
    """Test multi-intent detection"""
    print("\n" + "=" * 80)
    print("TEST 8: MULTI-INTENT DETECTION")
    print("=" * 80)
    
    test_cases = [
        "show me perfumes and add to wishlist",
        "I want to browse products and then checkout",
        "find attars, compare them, and add to cart",
    ]
    
    for query in test_cases:
        result = classify_intent(query, use_hybrid=True)
        print(f"\nQuery: '{query}'")
        print(f"  Primary: {result.category.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        
        if 'combined_scores' in result.metadata:
            top_3 = sorted(result.metadata['combined_scores'].items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"  Top 3 intents:")
            for intent, score in top_3:
                print(f"    - {intent}: {score:.2f}")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "#" * 80)
    print("# HYBRID INTENT CLASSIFIER - COMPREHENSIVE TEST SUITE")
    print("#" * 80)
    
    try:
        test_simple_queries()
        test_hybrid_mode()
        test_ambiguous_queries()
        test_entity_extraction()
        test_context_awareness()
        test_confidence_calibration()
        test_performance()
        test_multi_intent_detection()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
