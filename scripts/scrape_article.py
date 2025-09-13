import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup


def _extract_meta(soup: BeautifulSoup, names: list[str]) -> Optional[str]:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find(
            "meta", attrs={"name": name}
        )
        if tag and tag.get("content"):
            return tag.get("content").strip()
    return None


def _extract_date(soup: BeautifulSoup) -> Optional[str]:
    # Try common meta tags
    date = _extract_meta(
        soup,
        [
            "article:published_time",
            "og:article:published_time",
            "publish_date",
            "date",
            "citation_publication_date",
        ],
    )
    if date:
        return date

    # Try <time> tag
    time_tag = soup.find("time")
    if time_tag:
        if time_tag.get("datetime"):
            return time_tag.get("datetime").strip()
        text = time_tag.get_text(strip=True)
        if text:
            return text

    return None


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    # Prefer og:title
    title = _extract_meta(soup, ["og:title", "twitter:title"]) or None
    if title:
        return title
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return None


def _extract_content(soup: BeautifulSoup) -> str:
    # Try to target an <article> first
    article = soup.find("article")
    candidates = [article] if article else []

    # Then try common containers
    candidates.extend(
        soup.select(
            "main, .content, #content, .post, .article, .entry-content, .post-content"
        )
    )

    seen = set()
    for node in candidates:
        if not node or id(node) in seen:
            continue
        seen.add(id(node))
        text = node.get_text("\n", strip=True)
        # Heuristic: require a minimum length
        if text and len(text) >= 200:
            return text

    # Fallback to body text
    body = soup.body
    if body:
        return body.get_text("\n", strip=True)
    return soup.get_text("\n", strip=True)


def scrape(url: str, timeout: int = 20) -> Dict[str, Any]:
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    title = _extract_title(soup) or url
    date_str = _extract_date(soup)
    content = _extract_content(soup)

    payload: Dict[str, Any] = {
        "url": url,
        "title": title,
        "content": content,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }
    if date_str:
        payload["date"] = date_str
    return payload


def maybe_post_to_backend(payload: Dict[str, Any], ingest_url: Optional[str]) -> Optional[Dict[str, Any]]:
    if not ingest_url:
        return None
    # Backend expects {title, content}
    to_send = {"title": payload.get("title", ""), "content": payload.get("content", "")}
    r = requests.post(ingest_url, json=to_send, timeout=20)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {"status": r.status_code}


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape a news/article page and optionally ingest.")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument(
        "--post",
        dest="post",
        action="store_true",
        help="If set, POST the result to backend /ingest",
    )
    parser.add_argument(
        "--backend",
        dest="backend",
        default="http://127.0.0.1:8000",
        help="Backend base URL (default: http://127.0.0.1:8000)",
    )
    args = parser.parse_args()

    try:
        data = scrape(args.url)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

    ingest_result = None
    if args.post:
        try:
            ingest_url = args.backend.rstrip("/") + "/ingest"
            ingest_result = maybe_post_to_backend(data, ingest_url)
        except Exception as e:
            ingest_result = {"error": str(e)}

    output = {"article": data, "ingest": ingest_result}
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


