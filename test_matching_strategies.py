#!/usr/bin/env python3
"""
Test Different Matching Strategies in KeywordMatcher

Tests the three match types:
1. Exact matching - Perfect keyword match
2. Partial matching - Substring/partial word match
3. Fuzzy matching - Similar words with variations
"""

import sys
import os
sys.path.insert(0, 'src')

# Disable queue to avoid connection errors
os.environ['QUEUE_CONVO_PATH'] = ''

from intent_classifier.keyword_matcher import KeywordMatcher

print("=" * 80)
print("KEYWORD MATCHING STRATEGY TEST")
print("=" * 80)
print()

# Initialize matcher
matcher = KeywordMatcher()

# Test cases designed to trigger different match types
test_cases = [
    # Exact matches
    {
        "query": "add to cart",
        "description": "Exact phrase match",
        "expected_type": "exact"
    },
    {
        "query": "checkout now",
        "description": "Exact keyword 'checkout'",
        "expected_type": "exact"
    },
    {
        "query": "show me perfumes",
        "description": "Exact keyword 'show'",
        "expected_type": "exact"
    },
    
    # Partial matches (keywords within larger text)
    {
        "query": "I would like to add this item to my shopping cart please",
        "description": "Partial match - 'cart' within sentence",
        "expected_type": "partial/exact"
    },
    {
        "query": "can you help me checkout the items",
        "description": "Partial match - 'checkout' in context",
        "expected_type": "partial/exact"
    },
    
    # Potential fuzzy matches (variations, misspellings)
    {
        "query": "perfume",
        "description": "Singular vs plural variation",
        "expected_type": "exact/fuzzy"
    },
    {
        "query": "searching for rose scent",
        "description": "Different word forms - 'search' vs 'searching'",
        "expected_type": "partial/fuzzy"
    },
    {
        "query": "goodbye for now",
        "description": "Exact with extra words",
        "expected_type": "exact/partial"
    },
    
    # Multi-word exact matches
    {
        "query": "order history",
        "description": "Multi-word exact phrase",
        "expected_type": "exact"
    },
    {
        "query": "view my order history",
        "description": "Multi-word phrase in context",
        "expected_type": "exact"
    },
]

print(f"Testing {len(test_cases)} queries across different match types")
print("=" * 80)
print()

# Track statistics
match_type_counts = {"exact": 0, "partial": 0, "fuzzy": 0}

for i, test_case in enumerate(test_cases, 1):
    query = test_case["query"]
    description = test_case["description"]
    expected = test_case["expected_type"]
    
    print(f"{i}. {description}")
    print(f"   Query: \"{query}\"")
    print("-" * 80)
    
    result = matcher.match_intent(query)
    
    if result:
        print(f"   Intent: {result.intent_name}")
        print(f"   Action: {result.action_code}")
        print(f"   Confidence: {result.confidence_score:.3f}")
        print(f"   Best Match Type: {result.best_match_type}")
        print(f"   Processing Time: {result.processing_time_ms:.2f}ms")
        print(f"   Total Matches: {result.total_matches}")
        
        # Show individual keyword matches with their types
        if result.matched_keywords:
            print(f"   Matched Keywords:")
            for kw in result.matched_keywords[:5]:  # Show first 5
                print(f"      - '{kw.keyword}' ({kw.match_type}, conf: {kw.confidence:.2f})")
        
        # Track match type statistics
        match_type_counts[result.best_match_type] = match_type_counts.get(result.best_match_type, 0) + 1
        
        # Verify expected type
        if expected in result.best_match_type or result.best_match_type in expected:
            print(f"   [EXPECTED] Match type matches: {expected}")
        else:
            print(f"   [INFO] Expected {expected}, got {result.best_match_type}")
    else:
        print("   [NO MATCH]")
    
    print()

print("=" * 80)
print("MATCH TYPE STATISTICS")
print("=" * 80)
print()

total_matches = sum(match_type_counts.values())
for match_type, count in match_type_counts.items():
    percentage = (count / total_matches * 100) if total_matches > 0 else 0
    print(f"{match_type.upper():10s}: {count:2d} matches ({percentage:5.1f}%)")

print()
print("=" * 80)
print("STRATEGY COMPARISON TEST")
print("=" * 80)
print()

# Test same query with different variations to show strategy differences
base_query = "add to cart"
variations = [
    "add to cart",                    # Exact
    "ADD TO CART",                    # Case variation (should normalize to exact)
    "please add to cart",             # Extra words before
    "add to my cart",                 # Extra word in middle
    "add this to cart",               # Extra word in middle
    "adding to cart",                 # Word form variation
    "add cart",                       # Missing word (should still partial match)
]

print("Testing query variations for 'add to cart':")
print("-" * 80)

for variation in variations:
    result = matcher.match_intent(variation)
    if result:
        match_types = set([m.match_type for m in result.matched_keywords])
        match_types_str = ", ".join(sorted(match_types))
        print(f"{variation:30s} -> {result.best_match_type:7s} (uses: {match_types_str})")
    else:
        print(f"{variation:30s} -> NO MATCH")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
