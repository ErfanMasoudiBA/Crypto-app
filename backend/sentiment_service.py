"""
Sentiment analysis service module.

This module handles all sentiment analysis functionality including
language detection, text analysis using rule-based analyzers,
and integration with translation services.
"""

import logging
from typing import Dict

import requests
from langdetect import DetectorFactory, detect
from sqlmodel import Session

from database import get_session
from models import Analysis, SentimentResult, SentimentScores
from rule_sentiment import analyze_text as rule_analyze_text
from rule_sentiment_en import analyze_text as rule_analyze_text_en

# Configure logging
logger = logging.getLogger(__name__)


def analyze_text_sentiment(text: str, session: Session) -> SentimentResult:
    """
    Analyze text sentiment and persist the result to database.
    
    Args:
        text: Text to analyze for sentiment
        session: Database session for persisting results
        
    Returns:
        SentimentResult: Sentiment analysis result with scores and metadata
    """
    raw_text = (text or "").strip()
    if not raw_text:
        empty_scores = {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
        return SentimentResult(
            text="",
            lang="und",
            label="neutral",
            scores=SentimentScores(**empty_scores),
            model="rule-v2",
        )

    # Ensure deterministic language detection
    DetectorFactory.seed = 0

    detected_lang = "und"
    try:
        detected_lang = detect(raw_text)
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        detected_lang = "und"

    analyzer_model = "rule-v2"
    analysis_dict: Dict[str, object]

    if detected_lang == "fa":
        # Use existing Persian rules as-is
        analysis_dict = rule_analyze_text(raw_text)
    else:
        # English or other languages handled with short English rules
        text_for_en = raw_text
        if detected_lang not in ("en", "und"):
            # Attempt on-demand translation if googletrans is installed; otherwise fallback
            try:
                from googletrans import Translator  # type: ignore
                translator = Translator()
                text_for_en = translator.translate(raw_text, dest="en").text or raw_text
                logger.info(f"Translated text from {detected_lang} to English")
            except Exception as e:
                logger.warning(f"Translation unavailable or failed: {e}")
                text_for_en = raw_text

        analysis_dict = rule_analyze_text_en(text_for_en)

    # Persist analysis (store original text and final scores/label)
    analysis = Analysis(
        text=raw_text,
        label=str(analysis_dict.get("label", "neutral")),
        positive=float(analysis_dict.get("scores", {}).get("positive", 0.0)),
        negative=float(analysis_dict.get("scores", {}).get("negative", 0.0)),
        neutral=float(analysis_dict.get("scores", {}).get("neutral", 1.0)),
    )
    session.add(analysis)
    session.commit()

    return SentimentResult(
        text=raw_text,
        lang=detected_lang,
        label=analysis.label,
        scores=SentimentScores(
            positive=analysis.positive,
            negative=analysis.negative,
            neutral=analysis.neutral,
        ),
        model=analyzer_model,
    )


def analyze_via_api(text: str) -> Dict[str, object]:
    """
    Analyze text sentiment via API call with fallback to local analysis.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dict[str, object]: Analysis result dictionary
    """
    try:
        resp = requests.post(
            "http://127.0.0.1:8000/analyze",
            json={"text": text},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"API call failed: {e}")
    
    # Fallback local analysis if API call fails
    try:
        detected_lang = "und"
        DetectorFactory.seed = 0
        try:
            detected_lang = detect(text)
        except Exception:
            detected_lang = "und"
            
        if detected_lang == "fa":
            return {
                **rule_analyze_text(text), 
                "text": text, 
                "lang": detected_lang, 
                "model": "rule-v2"
            }
        else:
            text_for_en = text
            if detected_lang not in ("en", "und"):
                # Attempt on-demand translation if available
                try:
                    from googletrans import Translator  # type: ignore
                    translator = Translator()
                    text_for_en = translator.translate(text, dest="en").text or text
                except Exception:
                    text_for_en = text
                    
            return {
                **rule_analyze_text_en(text_for_en), 
                "text": text, 
                "lang": detected_lang, 
                "model": "rule-v2"
            }
    except Exception as e:
        logger.error(f"Local analysis failed: {e}")
        return {
            "text": text, 
            "lang": "und", 
            "label": "neutral", 
            "scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0}, 
            "model": "rule-v2"
        }