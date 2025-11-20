#!/usr/bin/env python3
"""
Test Edge Case: Conversational Query
"i am going to a birthday party tommorow"

This query tests how the system handles:
1. General conversation (not product-related)
2. Fuzzy matching false positives
3. Low confidence thresholds
"""

import sys
import os
sys.path.insert(0, 'src')
os.environ['QUEUE_CONVO_PATH'] = ''

from orchestrator.orchestrator import classify_intent, orchestrate_query
from intent_classifier.keyword_matcher import KeywordMatcher

print("=" * 80)
print("EDGE CASE TEST: Conversational Non-Shopping Query")
print("=" * 80)
print()

query = "i am going to a birthday party tommorow"

print(f"Query: \"{query}\"")
print()

# Test 1: Direct KeywordMatcher
print("1. KEYWORD MATCHER ANALYSIS")
print("-" * 80)
matcher = KeywordMatcher()
result = matcher.match_intent(query)

if result:
    print(f"   Classified Intent: {result.intent_name}")
    print(f"   Action Code: {result.action_code}")
    print(f"   Confidence: {result.confidence_score:.3f}")
    print(f"   Match Type: {result.best_match_type}")
    print(f"   Processing Time: {result.processing_time_ms:.2f}ms")
    print()
    print("   Matched Keywords:")
    for i, kw in enumerate(result.matched_keywords[:10], 1):
        print(f"      {i}. \"{kw.keyword}\" (type: {kw.match_type}, confidence: {kw.confidence:.2f})")
    print()
    
    # Analyze the false positive
    if result.confidence_score < 0.8:
        print("   [ANALYSIS] LOW CONFIDENCE - Likely False Positive")
        print(f"   - This query was fuzzy-matched to '{result.intent_name}'")
        print(f"   - The word 'going' fuzzy-matches to 'join' in login intent")
        print(f"   - Confidence {result.confidence_score:.3f} < 0.8 threshold")
    else:
        print("   [ANALYSIS] HIGH CONFIDENCE")
else:
    print("   NO MATCH")

print()

# Test 2: Orchestrator classify_intent
print("2. ORCHESTRATOR INTENT CLASSIFICATION")
print("-" * 80)
intent_result = classify_intent(query, use_hybrid=True, context={})

if intent_result:
    print(f"   Category: {intent_result.category.value}")
    print(f"   Action Code: {intent_result.action_code.value}")
    print(f"   Confidence: {intent_result.confidence:.3f}")
    print(f"   Strategy: {intent_result.metadata.get('strategy')}")
    print()
    
    # Suggestion for handling
    if intent_result.confidence < 0.8:
        print("   [SUGGESTION] Consider adding confidence threshold check")
        print("   - Queries with confidence < 0.8 could be treated as UNKNOWN")
        print("   - Would prevent false positives in fuzzy matching")

print()

# Test 3: Full Orchestrator Pipeline
print("3. FULL ORCHESTRATOR RESPONSE")
print("-" * 80)
response = orchestrate_query(query, user_id='test', session_id='test')

print(f"   Response Length: {len(response)} characters")
print()
print("   Response Content:")
clean_response = response.replace('\n', ' ').replace('  ', ' ')
print(f"   {clean_response[:200]}...")

print()

# Test 4: Similar Queries
print("4. SIMILAR CONVERSATIONAL QUERIES")
print("-" * 80)

similar_queries = [
    "I'm looking for a gift",
    "I need something for a party",
    "what should I get for a birthday",
    "I'm just browsing",
    "tell me about your products",
]

print(f"{'Query':<40s} {'Intent':<20s} {'Confidence':<12s} {'Type'}")
print("-" * 80)

for sq in similar_queries:
    result = matcher.match_intent(sq)
    if result:
        print(f"{sq:<40s} {result.intent_name:<20s} {result.confidence_score:<12.3f} {result.best_match_type}")
    else:
        print(f"{sq:<40s} {'NO MATCH':<20s} {'':<12s} {'N/A'}")

print()

# Test 5: Recommendation
print("5. RECOMMENDATIONS")
print("-" * 80)
print()
print("ISSUE IDENTIFIED:")
print("  - Fuzzy matching can create false positives with low confidence")
print("  - 'going' -> 'join' causes birthday party query to match LOGIN intent")
print("  - Confidence score of 0.740 indicates uncertainty")
print()
print("POTENTIAL SOLUTIONS:")
print()
print("  A. Add Confidence Threshold (Recommended)")
print("     - Reject fuzzy matches with confidence < 0.8")
print("     - Treat as UNKNOWN intent instead")
print("     - Route to general conversation handler")
print()
print("  B. Add CLARIFICATION Intent Category")
print("     - For low confidence matches (0.6-0.8)")
print("     - Ask user to clarify their intent")
print("     - Example: \"Did you mean to login, or are you looking for products?\"")
print()
print("  C. Add GENERAL_CONVERSATION Intent")
print("     - Catch general chat that's not shopping-related")
print("     - Route to conversational AI response")
print("     - Helps distinguish chat from shopping intents")
print()
print("  D. Improve Fuzzy Matching")
print("     - Increase minimum similarity threshold")
print("     - Add context-aware scoring")
print("     - Weight exact matches higher")
print()
print("CURRENT BEHAVIOR:")
print("  - System classifies as LOGIN (false positive)")
print("  - Proceeds to product search")
print("  - Finds no products")
print("  - Returns \"No products found\" message")
print()
print("IDEAL BEHAVIOR:")
print("  - Detect low confidence or non-shopping intent")
print("  - Respond conversationally")
print("  - Example: \"That sounds fun! Are you looking for a gift or something")
print("             to wear to the party?\"")
print()

print("=" * 80)
print("TEST COMPLETE - Edge Case Documented")
print("=" * 80)
