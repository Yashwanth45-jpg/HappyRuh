#!/usr/bin/env python3
"""Test KeywordMatcher integration"""

from intent_classifier.keyword_matcher import KeywordMatcher
import time

# Initialize matcher
start = time.time()
matcher = KeywordMatcher()
init_time = (time.time() - start) * 1000

print(f'✅ KeywordMatcher initialized in {init_time:.2f}ms')
print(f'✅ Loaded {len(matcher.intent_keywords)} intents')
print(f'✅ Total keywords: {len(matcher.keyword_trie.get_all_keywords())}')

# Test queries
test_queries = [
    'show me perfumes under 5000',
    'add to cart',
    'what is the price',
    'checkout',
    'hello',
    'show my orders',
    'i want a refund'
]

print('\n🧪 Testing Sample Queries:')
print('=' * 60)

for query in test_queries:
    result = matcher.match_intent(query)
    if result:
        print(f'✅ "{query}"')
        print(f'   Intent: {result.intent_name} | Action: {result.action_code}')
        print(f'   Confidence: {result.confidence_score:.3f} | Time: {result.processing_time_ms:.2f}ms')
    else:
        print(f'❌ "{query}" -> No match found')
    print()

# Performance stats
stats = matcher.get_performance_stats()
print('📊 Performance Statistics:')
print(f'   Average time: {stats.get("avg_processing_time_ms", 0):.2f}ms')
print(f'   Queries under 50ms: {stats.get("queries_under_50ms_percentage", 0):.1f}%')
print(f'   Total queries: {stats.get("total_queries_processed", 0)}')
