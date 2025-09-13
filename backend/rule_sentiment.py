from __future__ import annotations

from typing import Dict


# Minimal Persian rule-based sentiment analyzer with emoji support
# This is intentionally simple and fast with small lexicons.

POSITIVE_WORDS = {
    "عالی",
    "خوب",
    "زیبا",
    "دوست‌داشتنی",
    "دوستداشتنی",
    "شاد",
    "امیدوار",
    "امیدبخش",
    "موفق",
    "موفقیت",
    "راضی",
    "مثبت",
    "رشد",
    "افزایش",
    "بهبود",
    "صعود",
    "صعودی",
    "خوشبین",
    "خوش‌بین",
    "خوشبینانه",
}

NEGATIVE_WORDS = {
    "بد",
    "افتضاح",
    "زشت",
    "نفرت",
    "متنفر",
    "غمگین",
    "ناراحت",
    "ناکام",
    "عصبانی",
    "منفی",
    "کاهش",
    "افت",
    "سقوط",
    "ریزش",
    "ضعیف",
    "ناامید",
    "دلواپس",
    "نگران",
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


def _simple_tokenize(text: str) -> list[str]:
    separators = "\n\t .,!?:;،؛()[]{}\"'«»\/|"
    tokens: list[str] = []
    current = []
    for ch in text:
        if ch in separators:
            if current:
                tokens.append("".join(current))
                current = []
            # keep emojis and standalone punctuation as separate tokens
            if ch.strip() and ch in EMOJI_TO_SCORE:
                tokens.append(ch)
        else:
            # keep emojis as their own tokens
            if ch in EMOJI_TO_SCORE:
                if current:
                    tokens.append("".join(current))
                    current = []
                tokens.append(ch)
            else:
                current.append(ch)
    if current:
        tokens.append("".join(current))
    return tokens


def analyze_text(text: str) -> Dict[str, object]:
    if not text:
        return {"label": "neutral", "scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0}}

    tokens = _simple_tokenize(text)

    positive_hits = 0
    negative_hits = 0

    for tok in tokens:
        normalized = tok.strip().lower()
        if not normalized:
            continue
        if tok in EMOJI_TO_SCORE:
            if EMOJI_TO_SCORE[tok] > 0:
                positive_hits += 1
            elif EMOJI_TO_SCORE[tok] < 0:
                negative_hits += 1
            continue
        if normalized in (w.lower() for w in POSITIVE_WORDS):
            positive_hits += 1
            continue
        if normalized in (w.lower() for w in NEGATIVE_WORDS):
            negative_hits += 1

    # Heuristic keyword scanning for common market phrases (Persian)
    lowered = text.strip().lower()
    positive_keywords = [
        "رشد", "افزایش", "صعود", "خوشبین", "امید", "امیدبخش", "بهبود", "مثبت", "رونق", "بازگشت",
    ]
    negative_keywords = [
        "کاهش", "افت", "سقوط", "ریزش", "نگران", "ترس", "ضعیف", "منفی", "رکود", "خروج سرمایه",
    ]
    for kw in positive_keywords:
        if kw in lowered:
            positive_hits += 1
    for kw in negative_keywords:
        if kw in lowered:
            negative_hits += 1

    total_hits = positive_hits + negative_hits
    if total_hits == 0:
        scores = {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
        label = "neutral"
    else:
        pos_score = positive_hits / total_hits
        neg_score = negative_hits / total_hits
        neu_score = max(0.0, 1.0 - (pos_score + neg_score) / 1.0)
        scores = {"positive": round(pos_score, 4), "negative": round(neg_score, 4), "neutral": round(neu_score, 4)}
        if abs(pos_score - neg_score) < 0.15:
            label = "neutral"
        elif pos_score > neg_score:
            label = "positive"
        else:
            label = "negative"

    return {"label": label, "scores": scores}


