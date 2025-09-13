from __future__ import annotations

from typing import Dict


POSITIVE_WORDS = {
    "great",
    "good",
    "excellent",
    "amazing",
    "happy",
    "love",
    "like",
    "success",
    "satisfied",
    "win",
    "awesome",
    "gain",
    "gains",
    "rally",
    "surge",
    "bullish",
    "optimistic",
    "improve",
    "improved",
    "strong",
}

NEGATIVE_WORDS = {
    "bad",
    "terrible",
    "awful",
    "hate",
    "angry",
    "sad",
    "disappointed",
    "worse",
    "worst",
    "fail",
    "broken",
    "fall",
    "falls",
    "drop",
    "drops",
    "plunge",
    "bearish",
    "panic",
    "fear",
    "weak",
    "selloff",
}

EMOJI_TO_SCORE = {
    "👍": 1.0,
    "😊": 1.0,
    "😁": 1.0,
    "😍": 1.0,
    "❤️": 1.0,
    "🎉": 1.0,
    "👎": -1.0,
    "😞": -1.0,
    "😡": -1.0,
    "💔": -1.0,
    "😢": -1.0,
}


def analyze_text(text: str) -> Dict[str, object]:
    if not text:
        return {"label": "neutral", "scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0}}

    import re

    tokens = re.findall(r"[\w']+|[👍😊😁😍❤️🎉👎😞😡💔😢]", text.lower())

    pos_hits = 0
    neg_hits = 0
    for tok in tokens:
        if tok in EMOJI_TO_SCORE:
            if EMOJI_TO_SCORE[tok] > 0:
                pos_hits += 1
            elif EMOJI_TO_SCORE[tok] < 0:
                neg_hits += 1
            continue
        if tok in POSITIVE_WORDS:
            pos_hits += 1
            continue
        if tok in NEGATIVE_WORDS:
            neg_hits += 1

    total = pos_hits + neg_hits
    if total == 0:
        scores = {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
        label = "neutral"
    else:
        pos_score = pos_hits / total
        neg_score = neg_hits / total
        neu_score = max(0.0, 1.0 - (pos_score + neg_score))
        scores = {
            "positive": round(pos_score, 4),
            "negative": round(neg_score, 4),
            "neutral": round(neu_score, 4),
        }
        if abs(pos_score - neg_score) < 0.15:
            label = "neutral"
        elif pos_score > neg_score:
            label = "positive"
        else:
            label = "negative"

    return {"label": label, "scores": scores}


