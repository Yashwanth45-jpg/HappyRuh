"""
Test that intent metadata (needs_clarification, reasoning) is passed to LLM response generation.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator.orchestrator import orchestrate_query

def test_intent_metadata_flow():
    """Test that LLM intent metadata flows through to response generation."""
    
    print("\n" + "="*80)
    print("INTENT METADATA FLOW TEST")
    print("="*80)
    
    test_cases = [
        {
            'query': 'i am going to a birthday party tomorrow',
            'description': 'Non-shopping query (should trigger LLM classification)',
            'expected_strategy': 'hybrid_llm_validation'
        },
        {
            'query': 'show me rose perfumes',
            'description': 'Clear shopping query (high confidence keyword match)',
            'expected_strategy': 'keyword_matching'
        },
        {
            'query': 'I need something special',
            'description': 'Ambiguous query (may need clarification)',
            'expected_strategy': 'could be keyword or llm'
        }
    ]
    
    for idx, test_case in enumerate(test_cases, 1):
        query = test_case['query']
        description = test_case['description']
        
        print(f"\n{'='*80}")
        print(f"TEST {idx}: {description}")
        print(f"{'='*80}")
        print(f"Query: '{query}'")
        print(f"\nProcessing...")
        print("-"*80)
        
        try:
            # Call orchestrate_query which will classify intent and generate response
            response = orchestrate_query(
                user_query=query,
                user_id="test_user",
                session_id="test_session",
                chat_history=[]
            )
            
            print(f"\nResponse generated:")
            print(f"Length: {len(response)} chars")
            
            # Check if intent metadata context appears in debug logs
            # The logs should show "Passing intent metadata to LLM" if LLM was used for classification
            print(f"\nCheck the logs above to see if intent metadata was passed to LLM")
            
            # Show snippet of response
            clean_response = response.replace('<div', '\n<div').replace('</div>', '</div>\n')
            print(f"\nResponse preview (first 300 chars):")
            print(clean_response[:300] + "...")
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\nKey things to check in logs:")
    print("1. 'Low confidence (0.74) or fuzzy match - using LLM validation'")
    print("2. 'LLM intent classification output: CATEGORY: ...'")
    print("3. 'Passing intent metadata to LLM: {...}'")
    print("4. '[DEBUG] Intent metadata: {...}' in LLMConnector")
    print("\nIf you see these logs, the intent metadata is flowing correctly!")
    print("="*80)


if __name__ == "__main__":
    test_intent_metadata_flow()
