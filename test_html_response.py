"""Test HTML response format with collapsible product tags"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.orchestrator.orchestrator import orchestrate_query

# Test query
test_query = "show me perfumes for men"

print("\n" + "="*80)
print("TESTING HTML RESPONSE FORMAT WITH COLLAPSIBLE TAGS")
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

print("\n" + "-"*80)
print("FULL HTML RESPONSE:")
print("-"*80)
# Don't print response directly (Unicode issues on Windows)
print(f"Response length: {len(response)} characters")
print("-"*80)

# Save to file for browser preview
output_file = "test_html_response_output.html"
with open(output_file, 'w', encoding='utf-8') as f:
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test HTML Response</title>
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

print(f"\n[OK] Full HTML saved to: {output_file}")
print("   Open this file in a browser to see the interactive product tags!")

# Check for key elements
print("\n" + "="*80)
print("VALIDATION CHECKS:")
print("="*80)

checks = [
    ("HTML tags present", "<p>" in response or "<div>" in response),
    ("Product tags present", 'class="product-tag"' in response),
    ("Product links have href", "https://happyruh.in/products/" in response),
    ("Collapsible container present", 'class="product-tags-container"' in response or len(response.split('class="product-tag"')) <= 3),
    ("CSS styles included", "<style>" in response),
    ("JavaScript included", "<script>" in response or len(response.split('class="product-tag"')) <= 3)
]

for check_name, result in checks:
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status}: {check_name}")

print("\n" + "="*80)
