from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

import feedparser  # type: ignore


FEEDS_FILE = Path(__file__).parent / "feeds.txt"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def read_feeds(file_path: Path) -> List[str]:
    urls: List[str] = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def fetch_feed(url: str) -> List[Dict[str, str]]:
    parsed = feedparser.parse(url)
    items: List[Dict[str, str]] = []
    for entry in parsed.entries:
        title = normalize_text(getattr(entry, "title", ""))
        link = normalize_text(getattr(entry, "link", ""))
        published = (
            normalize_text(getattr(entry, "published", ""))
            or normalize_text(getattr(entry, "updated", ""))
        )
        summary = normalize_text(getattr(entry, "summary", ""))

        # Some feeds put content in content[0].value
        if not summary and hasattr(entry, "content"):
            try:
                content_list = getattr(entry, "content")
                if content_list and isinstance(content_list, list):
                    summary = normalize_text(content_list[0].get("value", ""))
            except Exception:
                pass

        if not title and not link:
            continue
        items.append(
            {
                "title": title,
                "link": link,
                "published": published,
                "summary": summary,
                "source": url,
            }
        )
    return items


def dedupe_items(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen: Set[str] = set()
    unique: List[Dict[str, str]] = []
    for it in items:
        key = (it.get("link") or it.get("title") or "").strip()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        unique.append(it)
    return unique


def save_items(items: List[Dict[str, str]]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d")
    out_path = OUTPUT_DIR / f"{ts}.json"

    # Merge with existing file same day if present
    existing: List[Dict[str, str]] = []
    if out_path.exists():
        try:
            with out_path.open("r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    merged = dedupe_items(existing + items)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    return out_path


def main() -> None:
    urls = read_feeds(FEEDS_FILE)
    all_items: List[Dict[str, str]] = []
    for url in urls:
        try:
            items = fetch_feed(url)
            all_items.extend(items)
        except Exception:
            # skip failing feed
            continue

    unique_items = dedupe_items(all_items)
    out = save_items(unique_items)
    print(f"Saved {len(unique_items)} items to {out}")


if __name__ == "__main__":
    main()


