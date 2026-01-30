"""
Generates ONE Turkish viral sentence for Reels.
Uses content pools with configurable distribution (emotional/sarcastic/deep/romantic).
No emojis, no end punctuation, no quotes. 8-12 words, modern Turkish.
"""
import random
from pathlib import Path

# Optional: API-based generation (set OPENAI_API_KEY in .env to enable)
try:
    import os
    _OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
except Exception:
    _OPENAI_KEY = ""

from src.content_pools import POOLS


def _weighted_category(distribution: dict) -> str:
    """Pick category according to distribution (e.g. emotional 0.4, sarcastic 0.3, ...)."""
    r = random.random()
    cumul = 0.0
    for category, weight in distribution.items():
        cumul += weight
        if r <= cumul:
            return category
    return list(distribution.keys())[-1]


def generate_sentence(
    distribution: dict | None = None,
    use_api: bool = False,
) -> str:
    """
    Generate one Turkish viral sentence.

    Args:
        distribution: e.g. {"emotional": 0.4, "sarcastic": 0.3, "deep": 0.2, "romantic": 0.1}.
                     If None, uses default 40/30/20/10.
        use_api: If True and OPENAI_API_KEY is set, use API for generation (else pool).

    Returns:
        Single sentence, no trailing punctuation, no emojis, no quotes.
    """
    if distribution is None:
        distribution = {
            "emotional": 0.40,
            "sarcastic": 0.30,
            "deep": 0.20,
            "romantic": 0.10,
        }

    if use_api and _OPENAI_KEY:
        return _generate_via_api(distribution)

    category = _weighted_category(distribution)
    pool = POOLS.get(category, POOLS["emotional"])
    return random.choice(pool).strip()


def _generate_via_api(distribution: dict) -> str:
    """Optional: generate one sentence via OpenAI. Falls back to pool on error."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=_OPENAI_KEY)
        cat = _weighted_category(distribution)
        prompt = (
            "Generate exactly ONE short viral sentence in Turkish for Instagram Reels. "
            "Style: " + cat + ". "
            "Rules: 8-12 words, modern daily Turkish, young audience. "
            "No emojis, no punctuation at end, no quotation marks. "
            "Not motivational, not fake quotes, not guru style. "
            "Real human thought. Output only the sentence, nothing else."
        )
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
        )
        text = (r.choices[0].message.content or "").strip()
        # Strip quotes and trailing punctuation if any
        for c in ('"', "'", ".", "!", "?"):
            text = text.rstrip(c)
        if 5 <= len(text.split()) <= 15 and text:
            return text
    except Exception:
        pass
    # Fallback to pool
    category = _weighted_category(distribution)
    pool = POOLS.get(category, POOLS["emotional"])
    return random.choice(pool).strip()


if __name__ == "__main__":
    for _ in range(5):
        print(generate_sentence())
