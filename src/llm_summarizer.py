# src/llm_summarizer.py

"""
Fast product description summarization using lightweight local models.
Dual approach: LM Studio for speed, Ollama as fallback.
"""
from ollama import Client
# 
import os
from typing import Optional

# LM Studio - Fast lightweight model for summarization (Using Ollama Qwen)
LMSTUDIO_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:11435")
LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "qwen2.5:1.5b")

# Ollama - More powerful but slower fallback
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_SUMMARIZER_MODEL", "qwen2.5:1.5b")

# Initialize Ollama clients
lmstudio_client = Client(host=LMSTUDIO_URL)
ollama_client = Client(host=OLLAMA_URL)


def summarize_with_lmstudio(long_text: str, max_sentences: int = 3) -> Optional[str]:
    """
    Fast summarization using Ollama with Qwen 2.5 1.5B.
    Responds in ~200-500ms.
    """
    if not long_text or long_text.strip() == "":
        return None

    prompt = f"""Analyze this product description and extract the 3 MOST IMPORTANT features in exactly 3 bullet points.

Guidelines:
- Read the ENTIRE description carefully
- Identify what makes this product unique and valuable
- Extract key benefits, uses, or characteristics
- Each bullet should be ONE clear sentence
- Focus on what customers care about most

Product description:
{long_text}

Summary (3 bullet points only):"""

    try:
        print(f"[Qwen Summarizer] Calling {LMSTUDIO_URL} with ollama client...")
        
        response = lmstudio_client.chat(
            model=LMSTUDIO_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a product copywriter. Create very concise 3-point summaries. Each point should be ONE sentence maximum. Be brief and direct.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={
                'temperature': 0.2,
                'num_predict': 100
            }
        )
        
        summary = response['message']['content'].strip()
        
        if summary:
            print(f"[Qwen Summarizer] ✓ Generated summary ({len(summary)} chars)")
            return summary
        
        return None

    except Exception as e:
        print(f"[Qwen Summarizer] Error: {e}")
        return None


def summarize_with_ollama(long_text: str) -> Optional[str]:
    """
    Summarization using Ollama (qwen2.5:1.5b or fallback).
    """
    if not long_text or long_text.strip() == "":
        return None

    prompt = f"""Summarize this product in exactly 3 bullet points (one sentence each):
• Main features (describe what makes it special)
• Key ingredients/notes (list 2-3 main components)
• Best for (who should use this)

Product description:
{long_text}

Summary (3 bullet points only):"""

    try:
        print(f"[Ollama Summarizer] Calling {OLLAMA_URL} with ollama client...")
        
        response = ollama_client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={
                'temperature': 0.2,
                'num_predict': 100
            }
        )
        
        summary = response['response'].strip()
        
        if summary:
            print(f"[Ollama Summarizer] ✓ Generated summary ({len(summary)} chars)")
            return summary
        
        return None

    except Exception as e:
        print(f"[Ollama Summarizer] Error: {e}")
        return None


def summarize_description(long_text: str, prefer_fast: bool = True) -> str:
    """
    Main summarization function with dual LLM approach.
    
    Args:
        long_text: Product description to summarize
        prefer_fast: If True, tries LM Studio first (faster). If False, uses Ollama directly.
    
    Returns:
        Summarized description
    """
    if not long_text or long_text.strip() == "":
        return ""
    
    # If description is already short, return it
    if len(long_text) <= 200:
        return long_text.strip()
    
    # Try fast LLM first (LM Studio)
    if prefer_fast:
        summary = summarize_with_lmstudio(long_text)
        if summary:
            return summary
        print("[Summarizer] LM Studio unavailable, falling back to Ollama...")
    
    # Fallback to Ollama
    # summary = summarize_with_ollama(long_text)
    
    # If summarization completely failed, return first 200 chars of original
    if not summary or summary == "...":
        print("[Summarizer] Both LLMs failed, using original description (truncated)")
        return long_text[:200].strip() + "..."
    
    return summary


def summarize_batch(descriptions: list, prefer_fast: bool = True) -> list:
    """
    Batch summarize multiple descriptions.
    
    Args:
        descriptions: List of descriptions to summarize
        prefer_fast: Use fast LLM (LM Studio) if available
    
    Returns:
        List of summarized descriptions
    """
    print(f"[Batch Summarizer] Processing {len(descriptions)} descriptions...")
    summaries = []
    
    for i, desc in enumerate(descriptions, 1):
        print(f"[Batch Summarizer] {i}/{len(descriptions)}")
        summary = summarize_description(desc, prefer_fast=prefer_fast)
        summaries.append(summary)
    
    print(f"[Batch Summarizer] ✓ Completed {len(summaries)} summaries")
    return summaries


# ============================
# CLI Testing
# ============================

if __name__ == "__main__":
    test_description = """
    Uplift is an energizing fragrance that uplifts with citrus top notes, floral heart notes of rose geranium and 
    jasmine sambac, and a warm woody base with sandalwood, patchouli, and vetiver. Perfect for boosting mood and 
    creating a positive atmosphere. Contains pure essential oils and natural ingredients.
    """
    
    print("=" * 60)
    print("TESTING FAST SUMMARIZATION (LM Studio)")
    print("=" * 60)
    fast_summary = summarize_description(test_description, prefer_fast=True)
    print(f"\nFast Summary:\n{fast_summary}\n")
    
    print("=" * 60)
    print("TESTING BATCH SUMMARIZATION")
    print("=" * 60)
    batch_descriptions = [test_description] * 3
    batch_summaries = summarize_batch(batch_descriptions, prefer_fast=True)
    for i, summary in enumerate(batch_summaries, 1):
        print(f"\n{i}. {summary}")

