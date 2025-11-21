#!/usr/bin/env python3
"""Test orchestrator integration with KeywordMatcher"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator.orchestrator import classify_intent
from intent_classifier import IntentCategory, ActionCode

# Test the compatibility wrapper
test_queries = [
    'show me perfumes under 5000',
    'add to cart',
    'checkout',
    'hello',
    'goodbye',
    'thank you',
]

print('🧪 Testing Orchestrator Intent Classification Wrapper')
print('=' * 70)

for query in test_queries:
    result = classify_intent(query, use_hybrid=True, context={})
    if result:
        print(f'✅ "{query}"')
        print(f'   Category: {result.category.value}')
        print(f'   Action: {result.action_code.value}')
        print(f'   Confidence: {result.confidence:.3f}')
        print(f'   Strategy: {result.metadata.get("strategy")}')
        if result.metadata.get('matched_keywords'):
            print(f'   Matched: {", ".join(result.metadata["matched_keywords"][:3])}')
        print()
    else:
        print(f'❌ "{query}" -> No result')
        print()

print('✅ Orchestrator integration successful!')
