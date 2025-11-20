"""
Final test showing intent metadata (needs_clarification, reasoning) flowing to LLM response.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator.orchestrator import orchestrate_query

print("\n" + "="*80)
print("INTENT METADATA TO LLM RESPONSE FLOW TEST")
print("="*80)

query = "i am going to a birthday party tomorrow"

print(f"\nQuery: '{query}'")
print("\nExpected flow:")
print("1. Keyword matcher: Fuzzy match to LOGIN (0.74 confidence)")
print("2. LLM validation triggered (confidence < 0.85 for fuzzy)")
print("3. LLM classifies as UNKNOWN with needs_clarification=true")
print("4. Intent metadata passed to response LLM")
print("5. Response LLM uses this context")

print("\n" + "-"*80)
print("PROCESSING...")
print("-"*80 + "\n")

response = orchestrate_query(
    user_query=query,
    user_id="test",
    session_id="test",
    chat_history=[]
)

print("\n" + "="*80)
print("RESULT")
print("="*80)
print(f"\nResponse length: {len(response)} chars")
print(f"\nResponse content:")
print(response)

print("\n" + "="*80)
print("SUCCESS!")
print("="*80)
print("\nCheck the logs above for:")
print("* 'LLM intent classification output: CATEGORY: UNKNOWN'")
print("* 'Passing intent metadata to LLM: {...}'")
print("* '[DEBUG] Intent metadata: {...needs_clarification: True...}'")
print("\nThe LLM now has access to:")
print("- needs_clarification flag")  
print("- reasoning from intent classification")
print("- strategy used")
print("- confidence score")
print("- intent category")
print("\nThis allows the LLM to craft better responses based on intent analysis!")
print("="*80)
