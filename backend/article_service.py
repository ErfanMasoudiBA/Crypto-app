"""
Article management service module.

This module handles article ingestion, storage, retrieval,
and integration with sentiment analysis for content processing.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

from sqlmodel import Session, select

from database import get_session
from models import Analysis, Article, ArticleCreate
from sentiment_service import analyze_via_api

# Configure logging
logger = logging.getLogger(__name__)


def create_article(article_data: ArticleCreate, session: Session) -> Article:
    """
    Create a new article in the database.
    
    Args:
        article_data: Article creation data
        session: Database session
        
    Returns:
        Article: Created article with database ID
    """
    article = Article(title=article_data.title, content=article_data.content)
    session.add(article)
    session.commit()
    session.refresh(article)
    return article


def get_all_articles(session: Session) -> List[Article]:
    """
    Retrieve all articles from the database, ordered by creation date (newest first).
    
    Args:
        session: Database session
        
    Returns:
        List[Article]: List of all articles
    """
    statement = select(Article).order_by(Article.created_at.desc())
    results = session.exec(statement).all()
    return results


def ingest_article_with_analysis(article_json: Dict[str, object], session: Session = None) -> Dict[str, object]:
    """
    Create Article if new, analyze content via sentiment analysis API, and persist Analysis.

    The article_json can contain keys: title, content/summary, date/published, source, link.
    Deduplication is based on exact title match in the database.
    
    Args:
        article_json: Dictionary containing article data
        session: Optional database session (will create one if not provided)
        
    Returns:
        Dict[str, object]: Result dictionary with status and details
    """
    title = str(article_json.get("title", "")).strip()
    if not title:
        return {"status": "skipped", "reason": "missing_title"}
        
    content = str(
        article_json.get("content") or 
        article_json.get("summary") or 
        ""
    ).strip()
    if not content:
        return {"status": "skipped", "reason": "missing_content", "title": title}

    owns_session = False
    if session is None:
        owns_session = True
        session = next(get_session())

    try:
        # Deduplicate by title
        existing = session.exec(select(Article).where(Article.title == title)).first()
        if existing:
            return {"status": "exists", "title": title}

        # Create article
        article = Article(title=title, content=content)
        session.add(article)
        session.commit()
        session.refresh(article)

        # Analyze via sentiment analysis API
        result = analyze_via_api(content)
        scores = result.get("scores", {}) if isinstance(result, dict) else {}

        analysis = Analysis(
            text=content,
            label=str(result.get("label", "neutral")),
            positive=float(scores.get("positive", 0.0)),
            negative=float(scores.get("negative", 0.0)),
            neutral=float(scores.get("neutral", 1.0)),
        )
        session.add(analysis)
        session.commit()

        return {"status": "ingested", "title": title, "label": analysis.label}
        
    except Exception as e:
        logger.error(f"Error ingesting article '{title}': {e}")
        return {"status": "error", "title": title, "error": str(e)}
    finally:
        if owns_session:
            session.close()


def ingest_from_json_directory(data_dir: str = "data/raw", session: Session = None) -> Dict[str, object]:
    """
    Scan JSON files in a directory and ingest articles with sentiment analysis.
    
    Args:
        data_dir: Directory path containing JSON files with articles
        session: Optional database session
        
    Returns:
        Dict[str, object]: Summary of ingestion results
    """
    raw_dir = Path(data_dir)
    if not raw_dir.exists():
        return {"ingested": 0, "skipped": 0, "exists": 0, "errors": 0, "files": []}

    owns_session = False
    if session is None:
        owns_session = True
        session = next(get_session())

    ingested = 0
    skipped = 0
    exists = 0
    errors = 0
    processed_files: List[str] = []

    try:
        for file in sorted(raw_dir.glob("*.json")):
            try:
                with file.open("r", encoding="utf-8") as f:
                    items = json.load(f)
                    
                if not isinstance(items, list):
                    continue
                    
                for item in items:
                    if not isinstance(item, dict):
                        continue
                        
                    result = ingest_article_with_analysis(item, session=session)
                    status = result.get("status")
                    if status == "ingested":
                        ingested += 1
                    elif status == "exists":
                        exists += 1
                    elif status == "error":
                        errors += 1
                    else:
                        skipped += 1
                        
                processed_files.append(str(file))
                logger.info(f"Processed file: {file}")
                
            except Exception as e:
                logger.error(f"Error processing file {file}: {e}")
                errors += 1
                continue

    finally:
        if owns_session:
            session.close()

    return {
        "ingested": ingested, 
        "exists": exists, 
        "skipped": skipped, 
        "errors": errors,
        "files": processed_files
    }