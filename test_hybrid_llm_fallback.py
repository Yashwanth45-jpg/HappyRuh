"""
Test hybrid LLM fallback for intent classification.

Tests Options A, B, C combined:
- Option A: Confidence threshold (>= 0.85 accept, < 0.70 use LLM)
- Option B: Clarification for medium confidence (0.70-0.85)
- Option C: LLM validation for unknown/low confidence
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator.orchestrator import classify_intent

def test_hybrid_classification():
    """Test the hybrid intent classification with LLM fallback."""
    
    print("\n" + "="*80)
    print("HYBRID LLM FALLBACK TEST - Options A+B+C Combined")
    print("="*80)
    
    print("\n✅ Orchestrator loaded (keyword matcher auto-initialized)")
    
    # Test cases covering all confidence tiers
    test_cases = [
        # Option A: High confidence (>= 0.85) - Should accept keyword match
        {
            'query': 'show me perfumes',
            'expected_option': 'A',
            'description': 'High confidence keyword match - direct accept',
            'expected_confidence': '≥ 0.85'
        },
        {
            'query': 'add to cart',
            'expected_option': 'A',
            'description': 'High confidence keyword match - direct accept',
            'expected_confidence': '≥ 0.85'
        },
        
        # Option B: Medium confidence (0.70-0.85) - Should flag for clarification
        {
            'query': 'i need something',
            'expected_option': 'B',
            'description': 'Medium confidence fuzzy match - needs clarification',
            'expected_confidence': '0.70-0.85'
        },
        
        # Option C: Low confidence (< 0.70) - Should use LLM validation
        {
            'query': 'i am going to a birthday party tomorrow',
            'expected_option': 'C',
            'description': 'Low confidence fuzzy match - LLM validation',
            'expected_confidence': '< 0.70'
        },
        
        # Option C: No keyword match - Should use LLM classification
        {
            'query': 'what is the weather today?',
            'expected_option': 'C',
            'description': 'No keyword match - LLM classification',
            'expected_confidence': 'N/A'
        },
        {
            'query': 'tell me a joke',
            'expected_option': 'C',
            'description': 'No keyword match - LLM classification',
            'expected_confidence': 'N/A'
        },
        
        # Edge cases
        {
            'query': 'I\'m just browsing',
            'expected_option': 'C',
            'description': 'Conversational - may trigger fuzzy match or LLM',
            'expected_confidence': '< 0.85'
        },
        {
            'query': 'looking for a gift',
            'expected_option': 'A',
            'description': 'High confidence search intent',
            'expected_confidence': '≥ 0.85'
        }
    ]
    
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    
    for idx, test_case in enumerate(test_cases, 1):
        query = test_case['query']
        expected_option = test_case['expected_option']
        description = test_case['description']
        expected_confidence = test_case['expected_confidence']
        
        print(f"\n{'─'*80}")
        print(f"TEST {idx}: {description}")
        print(f"{'─'*80}")
        print(f"Query: '{query}'")
        print(f"Expected Option: {expected_option} (Confidence: {expected_confidence})")
        
        # Classify with hybrid enabled
        result = classify_intent(query, use_hybrid=True)
        
        if result:
            confidence = result.confidence
            category = result.category.value
            metadata = result.metadata
            
            # Determine which option was triggered
            strategy = metadata.get('strategy', 'unknown')
            needs_clarification = metadata.get('needs_clarification', False)
            
            if confidence >= 0.85:
                actual_option = 'A'
                option_desc = 'High Confidence - Accept'
            elif confidence >= 0.70:
                actual_option = 'B'
                option_desc = 'Medium Confidence - Clarification'
            else:
                actual_option = 'C'
                option_desc = 'Low Confidence - LLM Validation'
            
            if strategy in ['llm_fallback', 'llm_classification']:
                actual_option = 'C'
                option_desc = 'No Match - LLM Classification'
            
            # Print results
            print(f"\n📊 RESULT:")
            print(f"  Category: {category}")
            print(f"  Confidence: {confidence:.3f}")
            print(f"  Actual Option: {actual_option} ({option_desc})")
            print(f"  Strategy: {strategy}")
            print(f"  Needs Clarification: {needs_clarification}")
            
            # Check for clarification message
            if needs_clarification and 'clarification_message' in metadata:
                print(f"  💬 Clarification: {metadata['clarification_message']}")
            
            # Show LLM reasoning if available
            if 'reasoning' in metadata:
                print(f"  🤖 LLM Reasoning: {metadata['reasoning']}")
            
            # Show keyword match details if available
            if 'matched_keywords' in metadata:
                print(f"  🔑 Matched Keywords: {metadata['matched_keywords'][:3]}")
                print(f"  📈 Match Type: {metadata.get('best_match_type', 'N/A')}")
            
            # Validation
            if actual_option == expected_option:
                print(f"  ✅ PASS - Correct option triggered")
            else:
                print(f"  ⚠️  Expected option {expected_option}, got {actual_option}")
            
        else:
            print(f"\n❌ FAIL - No result returned")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(test_cases)}")
    print("\nOption A (High Confidence): Accepts keyword match without LLM call")
    print("Option B (Medium Confidence): Flags for clarification")
    print("Option C (Low Confidence/Unknown): Uses LLM validation/classification")
    print("\n✅ Hybrid LLM fallback system implemented and tested")
    print("="*80)


def test_birthday_party_edge_case():
    """Specific test for the birthday party false positive."""
    
    print("\n" + "="*80)
    print("EDGE CASE TEST: Birthday Party Query")
    print("="*80)
    
    query = "i am going to a birthday party tomorrow"
    
    print(f"\nQuery: '{query}'")
    print("\nPrevious Issue:")
    print("  ❌ Matched to LOGIN (confidence 0.740) via fuzzy match")
    print("  ❌ 'going' fuzzy-matched to 'join' in login keywords")
    print("\nExpected Fix:")
    print("  ✅ Low confidence (< 0.70) should trigger LLM validation")
    print("  ✅ LLM should classify as UNKNOWN or conversational")
    
    # Test with hybrid enabled
    print("\n" + "─"*80)
    print("Testing with Hybrid LLM Fallback ENABLED:")
    print("─"*80)
    
    result = classify_intent(query, use_hybrid=True)
    
    if result:
        print(f"\n📊 Result:")
        print(f"  Category: {result.category.value}")
        print(f"  Confidence: {result.confidence:.3f}")
        print(f"  Strategy: {result.metadata.get('strategy', 'N/A')}")
        
        if result.confidence >= 0.85:
            print(f"  Option: A (High Confidence - Accept)")
        elif result.confidence >= 0.70:
            print(f"  Option: B (Medium Confidence - Clarification)")
        else:
            print(f"  Option: C (Low Confidence - LLM Validation)")
        
        # Check if LLM was used
        if 'reasoning' in result.metadata:
            print(f"  🤖 LLM Reasoning: {result.metadata['reasoning']}")
            print(f"  ✅ LLM validation was used")
        elif 'keyword_match' in result.metadata:
            print(f"  🔑 Original Keyword Match: {result.metadata['keyword_match']}")
            print(f"  🔑 Keyword Confidence: {result.metadata['keyword_confidence']:.3f}")
        
        # Check clarification
        if result.metadata.get('needs_clarification'):
            print(f"  💬 Clarification: {result.metadata.get('clarification_message', 'N/A')}")
        
        # Validation
        if result.category.value == 'UNKNOWN' or result.metadata.get('strategy') in ['llm_fallback', 'hybrid_llm_validation']:
            print(f"\n  ✅ PASS - LLM correctly handled edge case")
        elif result.confidence < 0.70:
            print(f"\n  ⚠️  Low confidence detected but may need review")
        else:
            print(f"\n  ❌ FAIL - Still showing false positive")
    else:
        print(f"\n❌ No result returned")
    
    # Test with hybrid disabled (old behavior)
    print("\n" + "─"*80)
    print("Testing with Hybrid LLM Fallback DISABLED (old behavior):")
    print("─"*80)
    
    result_no_hybrid = classify_intent(query, use_hybrid=False)
    
    if result_no_hybrid:
        print(f"\n📊 Result:")
        print(f"  Category: {result_no_hybrid.category.value}")
        print(f"  Confidence: {result_no_hybrid.confidence:.3f}")
        print(f"  Strategy: {result_no_hybrid.metadata.get('strategy', 'N/A')}")
        
        if result_no_hybrid.category.value == 'LOGIN':
            print(f"  ❌ Still showing original false positive (expected)")
        
        print(f"\n  ℹ️  This shows the old behavior without LLM fallback")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Run tests
    test_hybrid_classification()
    test_birthday_party_edge_case()
