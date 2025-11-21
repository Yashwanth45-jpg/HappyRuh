"""Test HTML response with more products to verify collapsible tags"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.orchestrator.orchestrator import orchestrate_query

# Test query that should return many products
test_query = "show me all fragrances"

print("\n" + "="*80)
print("TESTING COLLAPSIBLE PRODUCT TAGS (MORE PRODUCTS)")
print("="*80)

print(f"\nQuery: {test_query}")
print("\nGenerating response...")

# Get response
response = orchestrate_query(
    user_query=test_query,
    user_id="test_user",
    session_id="test_session",
    chat_history=[]
)

print(f"\nResponse length: {len(response)} characters")

# Save to file
output_file = "test_collapsible_tags.html"
with open(output_file, 'w', encoding='utf-8') as f:
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Collapsible Tags Test</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .chat-container {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>Test Query: {test_query}</h2>
        <hr>
        {response}
    </div>
</body>
</html>"""
    f.write(html_template)

print(f"\nHTML saved to: {output_file}")

# Analyze the response
import re
tags = re.findall(r'<a[^>]*class="product-tag"[^>]*>.*?</a>', response)
hidden_tags = re.findall(r'class="product-tag hidden-tag"', response)
show_more = re.findall(r'class="show-more-btn"', response)

print("\n" + "="*80)
print("ANALYSIS:")
print("="*80)
print(f"Total product tags: {len(tags)}")
print(f"Hidden tags: {len(hidden_tags)}")
print(f"Show more buttons: {len(show_more)}")

if len(tags) > 2:
    print(f"\nExpected: 2 visible + {len(tags) - 2} hidden + 1 show-more button")
    print(f"Actual: {len(tags) - len(hidden_tags)} visible, {len(hidden_tags)} hidden, {len(show_more)} button(s)")
else:
    print(f"\nOnly {len(tags)} products - no collapsing needed")

print("\nProduct names:")
for i, tag in enumerate(tags[:5]):
    name = re.search(r'>([^<]+)</a>', tag)
    if name:
        hidden = "(hidden)" if i >= 2 else "(visible)"
        print(f"  {i+1}. {name.group(1)} {hidden}")

print("\n" + "="*80)
