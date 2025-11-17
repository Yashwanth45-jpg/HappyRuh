
# src/llm_summarizer.py

"""
Summarizes product descriptions using a local Ollama model.
Uses non-streaming mode to avoid token-by-token output.
"""

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"


def summarize_description(long_text: str) -> str:
    if not long_text or long_text.strip() == "":
        return ""

    prompt = f"""
You are an expert fragrance and wellness product copywriter.

Rewrite the product description into a *rich, complete, 1–2 sentence summary*.

The summary must:
- Include ALL key fragrance notes (citrus, florals, woods, amber, musk, spices, essential oils, etc.)
- Include important ingredients or oils mentioned in the description
- Mention the core benefit or effect (calming, energizing, uplifting, grounding, etc.)
- Sound elegant, smooth, and descriptive—not short or cut off
- NOT be shorter than 2 sentences
- NOT exceed 3 sentences
- NOT start with meta phrases like “Here is the summary”, “Summary:”, etc.
- Output ONLY the final summary.

Product Description:
\"\"\"{long_text}\"\"\" 

Final summary (ONLY the summary, no labels):
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )

        response.raise_for_status()

        data = response.json()
        return data.get("response", "").strip()

    except Exception as e:
        print(f"[Ollama Summarizer Error] {e}")
        return long_text[:200] + "..."

