import re
from html import unescape

TAG_RE = re.compile(r"<[^>]+>")

MD_PATTERNS = [
    (re.compile(r"(\*\*|__)(.*?)\1", re.S), r"\2"),   # **bold** or __bold__
    (re.compile(r"(\*|_)(.*?)\1", re.S), r"\2"),      # *em* or _em_
    (re.compile(r"^#{1,6}\s*", re.M), ""),            # # headings
    (re.compile(r"^>\s?", re.M), ""),                 # > blockquotes
    (re.compile(r"`{1,3}([^`]+)`{1,3}"), r"\1"),      # `code`
    (re.compile(r"!\[[^\]]*\]\([^)]+\)"), ""),        # images
    (re.compile(r"\[([^\]]+)\]\([^)]+\)"), r"\1"),    # [text](url)
]

def clean_text(text: str) -> str:
    if not text:
        return ""
    s = unescape(text)
    s = TAG_RE.sub(" ", s)
    for rx, repl in MD_PATTERNS:
        s = rx.sub(repl, s)
    return re.sub(r"\s+", " ", s).strip()

def parse_price_value(price_like) -> float | None:
    if price_like is None:
        return None
    s = str(price_like).replace(",", "")
    m = re.search(r"(\d+(\.\d+)?)", s)
    try:
        return float(m.group(1)) if m else None
    except Exception:
        return None


# def remove_unwanted_fields(product: dict) -> dict:
#     """
#     Remove unnecessary fields from product data.
#     Keep only essential fields for your application.
#     """
#     # Fields to keep
#     keep_fields = {
#         'id', 'title', 'body_html', 'product_type', 'handle',
#         'vendor', 'variants', 'image', 'images'
#     }
    
#     # Return only the fields we want
#     return {k: v for k, v in product.items() if k in keep_fields}
