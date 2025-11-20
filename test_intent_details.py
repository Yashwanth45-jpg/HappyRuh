#!/usr/bin/env python3
"""
Intent Classification Integration Test
Shows detailed intent classification results
"""

import sys
import os
sys.path.insert(0, 'src')

# Disable queue to avoid connection errors
os.environ['QUEUE_CONVO_PATH'] = ''

from orchestrator.orchestrator import classify_intent
from intent_classifier import IntentCategory, ActionCode

print("=" * 80)
print("DETAILED INTENT CLASSIFICATION TEST")
print("=" * 80)
print()

test_queries = [
    "Hello, I'm looking for perfumes",
    "show me rose perfumes under 5000 rupees",
    "add this to my cart",
    "I want to checkout now",
    "what are crystals good for?",
    "view my order history",
    "I need a refund",
    "thank you for your help",
    "goodbye"
]

for i, query in enumerate(test_queries, 1):
    print(f"{i}. Query: \"{query}\"")
    print("-" * 80)
    
    result = classify_intent(query, use_hybrid=True, context={})
    
    if result:
        print(f"   Category: {result.category.value}")
        print(f"   Action Code: {result.action_code.value}")
        print(f"   Confidence: {result.confidence:.3f}")
        print(f"   Strategy: {result.metadata.get('strategy', 'unknown')}")
        print(f"   Processing Time: {result.metadata.get('processing_time_ms', 0):.2f}ms")
        
        matched = result.metadata.get('matched_keywords', [])
        if matched:
            print(f"   Matched Keywords: {', '.join(matched[:5])}")
        
        print(f"   Total Matches: {result.metadata.get('total_matches', 0)}")
        print(f"   Best Match Type: {result.metadata.get('best_match_type', 'N/A')}")
    else:
        print("   [NO MATCH]")
    
    print()

print("=" * 80)
print("INTEGRATION TEST COMPLETE")
print("=" * 80)
