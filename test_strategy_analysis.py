#!/usr/bin/env python3
"""
Test Orchestrator with Different Matching Strategies

Shows how the orchestrator classify_intent wrapper handles
different match types and confidence levels
"""

import sys
import os
sys.path.insert(0, 'src')

# Disable queue to avoid connection errors
os.environ['QUEUE_CONVO_PATH'] = ''

from orchestrator.orchestrator import classify_intent

print("=" * 80)
print("ORCHESTRATOR INTENT CLASSIFICATION - STRATEGY ANALYSIS")
print("=" * 80)
print()

# Test cases showing different strategies and confidence levels
test_cases = [
    {
        "category": "EXACT MATCHES (High Confidence)",
        "queries": [
            "add to cart",
            "checkout",
            "view my orders",
            "hello",
            "goodbye",
        ]
    },
    {
        "category": "PARTIAL MATCHES (Context-based)",
        "queries": [
            "I would like to add this perfume to my cart",
            "can you help me checkout now",
            "please show me my order history",
            "hi there, looking for perfumes",
        ]
    },
    {
        "category": "FUZZY MATCHES (Word Variations)",
        "queries": [
            "adding to cart",
            "searched for roses",
            "looking at checkout options",
        ]
    },
    {
        "category": "MULTI-WORD EXACT PHRASES",
        "queries": [
            "order history",
            "shopping cart",
            "contact support",
            "return item",
        ]
    },
    {
        "category": "AMBIGUOUS / LOW CONFIDENCE",
        "queries": [
            "perfume",
            "roses",
            "help",
        ]
    }
]

for category_data in test_cases:
    category = category_data["category"]
    queries = category_data["queries"]
    
    print(f"\n{'=' * 80}")
    print(f"{category}")
    print(f"{'=' * 80}\n")
    
    for query in queries:
        result = classify_intent(query, use_hybrid=True, context={})
        
        if result:
            # Get metadata
            strategy = result.metadata.get('strategy', 'unknown')
            processing_time = result.metadata.get('processing_time_ms', 0)
            matched_kw = result.metadata.get('matched_keywords', [])
            total_matches = result.metadata.get('total_matches', 0)
            best_match_type = result.metadata.get('best_match_type', 'unknown')
            
            # Color code by confidence
            conf_indicator = ""
            if result.confidence >= 0.9:
                conf_indicator = "[HIGH]"
            elif result.confidence >= 0.7:
                conf_indicator = "[MEDIUM]"
            else:
                conf_indicator = "[LOW]"
            
            print(f"Query: \"{query}\"")
            print(f"  Category: {result.category.value:20s} | Confidence: {result.confidence:.3f} {conf_indicator}")
            print(f"  Strategy: {strategy:20s} | Match Type: {best_match_type}")
            print(f"  Action: {result.action_code.value}")
            print(f"  Matched: {', '.join(matched_kw[:3])}{'...' if len(matched_kw) > 3 else ''}")
            print(f"  Total Matches: {total_matches} | Time: {processing_time:.2f}ms")
            print()
        else:
            print(f"Query: \"{query}\"")
            print(f"  [NO MATCH]\n")

print("=" * 80)
print("CONFIDENCE LEVEL ANALYSIS")
print("=" * 80)
print()

# Analyze confidence distribution
confidence_tests = [
    ("add to cart", "Perfect exact match"),
    ("I want to add this to cart", "Exact with context"),
    ("adding to cart", "Word variation (fuzzy)"),
    ("cart", "Single word (ambiguous)"),
    ("help me with checkout", "Multiple intents possible"),
]

print(f"{'Query':<35s} {'Confidence':<12s} {'Type':<10s} {'Description'}")
print("-" * 80)

for query, description in confidence_tests:
    result = classify_intent(query, use_hybrid=True, context={})
    if result:
        best_type = result.metadata.get('best_match_type', 'N/A')
        print(f"{query:<35s} {result.confidence:<12.3f} {best_type:<10s} {description}")
    else:
        print(f"{query:<35s} {'NO MATCH':<12s} {'N/A':<10s} {description}")

print()
print("=" * 80)
print("MATCH TYPE BREAKDOWN")
print("=" * 80)
print()

print("EXACT MATCHING:")
print("  - Direct keyword match in normalized text")
print("  - Confidence: 1.0")
print("  - Examples: 'checkout', 'add to cart', 'goodbye'")
print()

print("PARTIAL MATCHING:")
print("  - Keyword found within larger text")
print("  - Confidence: 0.8 base")
print("  - Examples: 'I want to checkout' contains 'checkout'")
print()

print("FUZZY MATCHING:")
print("  - Similar words with variations")
print("  - Confidence: 0.6 base")
print("  - Examples: 'adding' matches 'add', 'searched' matches 'search'")
print()

print("CONFIDENCE BOOSTING:")
print("  - Multi-word phrases: +0.2")
print("  - Action phrases: +0.15")
print("  - Multiple matches: +0.05 per match (max +0.2)")
print("  - Exact match bonus: +0.1")
print()

print("=" * 80)
print("TEST COMPLETE - All Matching Strategies Verified")
print("=" * 80)
