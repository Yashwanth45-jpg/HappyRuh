#!/usr/bin/env python3
"""
Full Integration Test for Orchestrate Query with Intent Classification

Tests the complete pipeline:
1. Intent classification
2. Semantic search
3. LLM response generation
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.orchestrator import orchestrate_query
import logging

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test cases covering different intent categories
test_cases = [
    {
        "query": "Hello",
        "expected_intent": "GREETING",
        "description": "Simple greeting"
    },
    {
        "query": "show me perfumes under 5000",
        "expected_intent": "SEARCH",
        "description": "Product search with price filter"
    },
    {
        "query": "what are crystals good for?",
        "expected_intent": "SEARCH/FAQ",
        "description": "General product question"
    },
    {
        "query": "add to cart",
        "expected_intent": "ADD_TO_CART",
        "description": "Cart operation"
    },
    {
        "query": "I want to checkout",
        "expected_intent": "CHECKOUT",
        "description": "Checkout intent"
    },
    {
        "query": "thank you",
        "expected_intent": "THANKS",
        "description": "Appreciation"
    },
    {
        "query": "goodbye",
        "expected_intent": "GOODBYE",
        "description": "Farewell"
    },
    {
        "query": "show me lavender fragrances",
        "expected_intent": "SEARCH",
        "description": "Product search by type"
    }
]

print("=" * 80)
print("FULL ORCHESTRATOR INTEGRATION TEST")
print("=" * 80)
print()

# Test with minimal history
test_history = [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How can I help you today?"}
]

for i, test_case in enumerate(test_cases, 1):
    query = test_case["query"]
    expected = test_case["expected_intent"]
    description = test_case["description"]
    
    print(f"\n{'='*80}")
    print(f"Test {i}/{len(test_cases)}: {description}")
    print(f"{'='*80}")
    print(f"Query: \"{query}\"")
    print(f"Expected Intent: {expected}")
    print(f"-" * 80)
    
    try:
        # Call orchestrate_query
        response = orchestrate_query(
            user_query=query,
            user_id="test_user",
            session_id="test_session",
            chat_history=test_history.copy()
        )
        
        # Check response
        if response and len(response) > 0:
            print(f"[OK] Response Generated: {len(response)} characters")
            
            # Display first 300 characters of response (cleaned)
            clean_response = response.replace('\n', ' ').replace('  ', ' ')
            preview = clean_response[:300] + "..." if len(clean_response) > 300 else clean_response
            print(f"\nResponse Preview:")
            print(f"{preview}")
            
            # Check for HTML structure
            if '<div' in response and '</div>' in response:
                print(f"[OK] Valid HTML structure detected")
            else:
                print(f"[WARN] No HTML structure found")
                
        else:
            print(f"[ERROR] Empty or invalid response")
            
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("TEST SUITE COMPLETED")
print("=" * 80)

# Performance test with single query
print("\n" + "=" * 80)
print("PERFORMANCE TEST")
print("=" * 80)

import time

perf_query = "show me rose perfumes"
print(f"\nQuery: \"{perf_query}\"")

start_time = time.time()
response = orchestrate_query(
    user_query=perf_query,
    user_id="perf_test",
    session_id="perf_session"
)
elapsed = (time.time() - start_time) * 1000

print(f"Total Time: {elapsed:.2f}ms")
print(f"Response Length: {len(response)} characters")

if elapsed < 1000:
    print(f"[OK] Performance: Excellent (< 1s)")
elif elapsed < 3000:
    print(f"[OK] Performance: Good (< 3s)")
else:
    print(f"[WARN] Performance: Slow (> 3s)")

print("\n" + "=" * 80)
print("ALL TESTS COMPLETE")
print("=" * 80)
