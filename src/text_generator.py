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
    return_category: bool = False,
):
    """
    Generate one Turkish viral sentence.

    Args:
        distribution: e.g. {"emotional": 0.4, "sarcastic": 0.3, "deep": 0.2, "romantic": 0.1}.
                     If None, uses default 40/30/20/10.
        use_api: If True and OPENAI_API_KEY is set, use API for generation (else pool).
        return_category: If True, return (sentence, category) for music-matching.

    Returns:
        Single sentence, or (sentence, category) if return_category=True.
    """
    if distribution is None:
        distribution = {
            "emotional": 0.40,
            "sarcastic": 0.30,
            "deep": 0.20,
            "romantic": 0.10,
        }

    if use_api and _OPENAI_KEY:
        text, cat = _generate_via_api(distribution)
        return (text, cat) if return_category else text

    category = _weighted_category(distribution)
    pool = POOLS.get(category, POOLS["emotional"])
    sentence = random.choice(pool).strip()
    return (sentence, category) if return_category else sentence


def _generate_via_api(distribution: dict) -> tuple[str, str]:
    """Optional: generate one sentence via OpenAI. Returns (text, category). Falls back to pool on error."""
    cat = _weighted_category(distribution)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=_OPENAI_KEY)
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
        for c in ('"', "'", ".", "!", "?"):
            text = text.rstrip(c)
        if 5 <= len(text.split()) <= 15 and text:
            return (text, cat)
    except Exception:
        pass
    pool = POOLS.get(cat, POOLS["emotional"])
    return (random.choice(pool).strip(), cat)


if __name__ == "__main__":
    for _ in range(5):
        print(generate_sentence())
