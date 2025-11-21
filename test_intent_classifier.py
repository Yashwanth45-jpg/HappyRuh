"""
Test script for Intent Classifier

Run this to verify the intent classification system is working correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intent_classifier import classify_intent, IntentCategory

def test_intent_classifier():
    """Test the intent classifier with various queries"""
    
    test_queries = [
        # Greetings
        "hi",
        "hello there",
        "good morning",
        
        # Product search
        "show me perfumes",
        "i want to buy attar",
        "looking for crystals",
        "find fragrance for party",
        
        # Price filters
        "perfumes under 500",
        "show me products between 100 and 300",
        "cheap fragrances",
        
        # Product info
        "tell me about this product",
        "what is this perfume",
        
        # Recommendations
        "recommend something for wedding",
        "what should i buy for office",
        
        # Cart
        "show my cart",
        "view cart",
        
        # Orders
        "my orders",
        "track my order",
        
        # Thanks & Goodbye
        "thank you",
        "bye",
    ]
    
    print("=" * 80)
    print("INTENT CLASSIFICATION TEST")
    print("=" * 80)
    
    for query in test_queries:
        result = classify_intent(query)
        
        print(f"\nQuery: '{query}'")
        print(f"  Category: {result.category.value}")
        print(f"  Action: {result.action_code.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        
        if result.entities:
            print(f"  Entities: {result.entities}")
        
        print(f"  Processing time: {result.processing_time_ms:.2f}ms")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_intent_classifier()
