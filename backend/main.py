from datetime import datetime
from typing import Generator, List, Optional, Dict, Any
import json
from pathlib import Path
import os
import requests
import time
import logging

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

from rule_sentiment import analyze_text as rule_analyze_text
from rule_sentiment_en import analyze_text as rule_analyze_text_en
from langdetect import detect, DetectorFactory
from googletrans import Translator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# How to run the server (development):
#   uvicorn main:app --reload


class Article(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ArticleCreate(SQLModel):
    title: str
    content: str


class AnalyzeRequest(BaseModel):
    text: str


class ChatRequest(BaseModel):
    message: str


class SentimentScores(BaseModel):
    positive: float
    negative: float
    neutral: float


class SentimentResult(BaseModel):
    text: str
    lang: str
    label: str
    scores: SentimentScores
    model: str


# Crypto API Models
class CryptoCoin(BaseModel):
    rank: Optional[int]
    symbol: str
    id: str
    name: str
    price_usd: Optional[float]
    market_cap_usd: Optional[float]
    change_24h_pct: Optional[float]
    total_volume_usd: Optional[float]
    last_updated: Optional[str]


class CryptoResponse(BaseModel):
    coins: List[CryptoCoin]
    total_count: int
    last_updated: str
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class Analysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    label: str
    positive: float
    negative: float
    neutral: float
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


# Crypto API Constants
COINGECKO_MARKETS = "https://api.coingecko.com/api/v3/coins/markets"
PER_PAGE = 250
MAX_COINS = 1000
RETRY_DELAY = 15
REQUEST_DELAY = 5

sqlite_url = "sqlite:///app.db"
engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


# Crypto API Functions
def fetch_coins_from_coingecko() -> List[Dict[str, Any]]:
    """
    Fetch top 1000 cryptocurrencies from CoinGecko API with rate limiting.
    """
    all_coins = []
    page = 1
    
    while len(all_coins) < MAX_COINS:
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": PER_PAGE,
            "page": page,
            "sparkline": "false"
        }
        
        # Retry logic for rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching page {page} (attempt {attempt + 1})")
                response = requests.get(COINGECKO_MARKETS, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                break
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    wait_time = RETRY_DELAY * (attempt + 1)  # Exponential backoff
                    logger.warning(f"Rate limit hit on page {page}, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    if attempt == max_retries - 1:
                        raise HTTPException(
                            status_code=429, 
                            detail="CoinGecko API rate limit exceeded. Please try again later."
                        )
                else:
                    logger.error(f"HTTP error on page {page}: {e}")
                    raise HTTPException(status_code=response.status_code, detail=str(e))
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on page {page}: {e}")
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=500, detail="Failed to fetch data from CoinGecko")
                time.sleep(5)
        
        if not data:
            logger.info("No more data available")
            break
            
        all_coins.extend(data)
        logger.info(f"Page {page} completed, total coins: {len(all_coins)}")
        
        # Limit to MAX_COINS
        if len(all_coins) >= MAX_COINS:
            all_coins = all_coins[:MAX_COINS]
            break
            
        page += 1
        time.sleep(REQUEST_DELAY)  # Delay between requests
    
    return all_coins


def fetch_coins_from_coingecko_paginated(page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch a specific page of cryptocurrencies from CoinGecko API with rate limiting.
    """
    # Validate inputs
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if per_page < 1 or per_page > 250:
        raise HTTPException(status_code=400, detail="Per page must be between 1 and 250")
    
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
        "sparkline": "false"
    }
    
    # Retry logic for rate limiting
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching page {page} with {per_page} items (attempt {attempt + 1})")
            response = requests.get(COINGECKO_MARKETS, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            break
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                wait_time = RETRY_DELAY * (attempt + 1)  # Exponential backoff
                logger.warning(f"Rate limit hit on page {page}, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=429, 
                        detail="CoinGecko API rate limit exceeded. Please try again later."
                    )
            else:
                logger.error(f"HTTP error on page {page}: {e}")
                raise HTTPException(status_code=response.status_code, detail=str(e))
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error on page {page}: {e}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail="Failed to fetch data from CoinGecko")
            time.sleep(5)
    
    if not data:
        logger.info("No data available for the requested page")
        return []
    
    logger.info(f"Successfully fetched {len(data)} coins for page {page}")
    return data


def transform_coin_data(coin_data: Dict[str, Any]) -> CryptoCoin:
    """
    Transform raw CoinGecko data to our API format.
    """
    return CryptoCoin(
        rank=coin_data.get("market_cap_rank"),
        symbol=coin_data.get("symbol", "").upper(),
        id=coin_data.get("id", ""),
        name=coin_data.get("name", ""),
        price_usd=coin_data.get("current_price"),
        market_cap_usd=coin_data.get("market_cap"),
        change_24h_pct=coin_data.get("price_change_percentage_24h"),
        total_volume_usd=coin_data.get("total_volume"),
        last_updated=coin_data.get("last_updated")
    )


app = FastAPI(
    title="Unified API",
    description="Combined sentiment analysis and cryptocurrency API",
    version="1.0.0"
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/")
def read_root() -> dict:
    return {
        "message": "Unified API is running",
        "endpoints": {
            "sentiment": ["/ingest", "/articles", "/analyze", "/chat"],
            "crypto": ["/cryptos", "/cryptos/top/{limit}"]
        },
    }


@app.get("/favicon.ico")
def favicon() -> Response:
    # Avoid noisy 404s in logs for browsers requesting favicon
    return Response(status_code=204)


@app.post("/ingest", response_model=Article)
def ingest_article(payload: ArticleCreate, session: Session = Depends(get_session)) -> Article:
    article = Article(title=payload.title, content=payload.content)
    session.add(article)
    session.commit()
    session.refresh(article)
    return article


@app.get("/articles", response_model=List[Article])
def list_articles(session: Session = Depends(get_session)) -> List[Article]:
    statement = select(Article).order_by(Article.created_at.desc())
    results = session.exec(statement).all()
    return results


@app.post("/analyze", response_model=SentimentResult)
def analyze_endpoint(payload: AnalyzeRequest, session: Session = Depends(get_session)) -> SentimentResult:
    raw_text = (payload.text or "").strip()
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
    except Exception:
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
            try:
                translator = Translator()
                text_for_en = translator.translate(raw_text, dest="en").text or raw_text
            except Exception:
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


# english rules now live in backend.rule_sentiment_en


def _analyze_via_api(text: str) -> Dict[str, object]:
    try:
        resp = requests.post(
            "http://127.0.0.1:8000/analyze",
            json={"text": text},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    # Fallback local analysis if API call fails
    try:
        detected_lang = "und"
        DetectorFactory.seed = 0
        try:
            detected_lang = detect(text)
        except Exception:
            detected_lang = "und"
        if detected_lang == "fa":
            return {**rule_analyze_text(text), "text": text, "lang": detected_lang, "model": "rule-v2"}
        else:
            text_for_en = text
            if detected_lang not in ("en", "und"):
                try:
                    translator = Translator()
                    text_for_en = translator.translate(text, dest="en").text or text
                except Exception:
                    text_for_en = text
            return {**rule_analyze_text_en(text_for_en), "text": text, "lang": detected_lang, "model": "rule-v2"}
    except Exception:
        return {"text": text, "lang": "und", "label": "neutral", "scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0}, "model": "rule-v2"}


def ingest_article(article_json: Dict[str, object], session: Session | None = None) -> Dict[str, object]:
    """Create `Article` if new, analyze content via /analyze API, and persist `Analysis`.

    The `article_json` can contain keys: title, content/summary, date/published, source, link.
    Deduplication is based on exact title match in the DB.
    """
    title = str(article_json.get("title", "")).strip()
    if not title:
        return {"status": "skipped", "reason": "missing_title"}
    content = str(
        article_json.get("content")
        or article_json.get("summary")
        or ""
    ).strip()
    if not content:
        return {"status": "skipped", "reason": "missing_content", "title": title}

    owns_session = False
    if session is None:
        owns_session = True
        session = next(get_session())

    # Deduplicate by title
    existing = session.exec(select(Article).where(Article.title == title)).first()
    if existing:
        if owns_session:
            session.close()  # type: ignore[attr-defined]
        return {"status": "exists", "title": title}

    # Create article
    article = Article(title=title, content=content)
    session.add(article)
    session.commit()
    session.refresh(article)

    # Analyze via API
    result = _analyze_via_api(content)
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

    if owns_session:
        session.close()  # type: ignore[attr-defined]

    return {"status": "ingested", "title": title, "label": analysis.label}


@app.post("/ingest_feeds")
def ingest_from_raw_directory(session: Session = Depends(get_session)) -> Dict[str, object]:
    """Scan data/raw/*.json and ingest new articles, analyzing each only once by title."""
    raw_dir = Path("data") / "raw"
    if not raw_dir.exists():
        return {"ingested": 0, "skipped": 0, "exists": 0, "files": []}

    ingested = 0
    skipped = 0
    exists = 0
    processed_files: List[str] = []

    for file in sorted(raw_dir.glob("*.json")):
        try:
            with file.open("r", encoding="utf-8") as f:
                items = json.load(f)
            if not isinstance(items, list):
                continue
            for it in items:
                if not isinstance(it, dict):
                    continue
                res = ingest_article(it, session=session)
                status = res.get("status")
                if status == "ingested":
                    ingested += 1
                elif status == "exists":
                    exists += 1
                else:
                    skipped += 1
            processed_files.append(str(file))
        except Exception:
            continue

    return {"ingested": ingested, "exists": exists, "skipped": skipped, "files": processed_files}


@app.post("/chat")
def chat_with_bot(request: ChatRequest) -> Dict[str, str]:
    """Simple chatbot endpoint that provides contextual responses."""
    message = request.message.lower().strip()
    
    # Simple response logic based on message content
    if any(word in message for word in ["hello", "hi", "hey", "greetings"]):
        response = "Hello! How can I help you today?"
    elif any(word in message for word in ["how", "what", "why", "when", "where", "who"]):
        response = "That's an interesting question! I'm here to help you find answers."
    elif any(word in message for word in ["help", "assist", "support"]):
        response = "I'd be happy to help! What specific information do you need?"
    elif any(word in message for word in ["thank", "thanks"]):
        response = "You're welcome! Is there anything else I can help you with?"
    elif any(word in message for word in ["bye", "goodbye", "see you"]):
        response = "Goodbye! Have a great day!"
    else:
        response = "I understand what you're saying. Could you tell me more about what you'd like to know?"
    
    return {"response": response}


# Crypto API Endpoints
@app.get("/cryptos", response_model=CryptoResponse, summary="Get Paginated Cryptocurrencies")
async def get_cryptos(page: int = 1, per_page: int = 10):
    """
    Fetch and return a paginated list of cryptocurrencies from CoinGecko.
    
    Args:
        page: Page number (default: 1, minimum: 1)
        per_page: Number of items per page (default: 10, range: 1-250)
    
    Returns:
        - List of cryptocurrencies with rank, symbol, name, price, market cap, etc.
        - Pagination metadata (page, per_page, total_pages, has_next, has_prev)
        - Last updated timestamp
    """
    try:
        logger.info(f"Starting to fetch cryptocurrency data - page {page}, per_page {per_page}")
        
        # Validate inputs
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if per_page < 1 or per_page > 250:
            raise HTTPException(status_code=400, detail="Per page must be between 1 and 250")
        
        # Fetch only the requested page
        raw_coins = fetch_coins_from_coingecko_paginated(page, per_page)
        
        if not raw_coins:
            raise HTTPException(status_code=404, detail="No cryptocurrency data found for the requested page")
        
        # Transform data to our format
        transformed_coins = [transform_coin_data(coin) for coin in raw_coins]
        
        # Get the most recent last_updated timestamp
        last_updated = max(
            (coin.last_updated for coin in transformed_coins if coin.last_updated), 
            default=""
        )
        
        # Calculate pagination metadata
        # Note: We don't know the total count without fetching all data, so we'll estimate
        # For a more accurate count, we could make a separate API call or cache the total
        estimated_total = 1000  # CoinGecko typically has around 1000+ coins
        total_pages = (estimated_total + per_page - 1) // per_page  # Ceiling division
        
        has_next = page < total_pages
        has_prev = page > 1
        
        logger.info(f"Successfully fetched {len(transformed_coins)} cryptocurrencies for page {page}")
        
        return CryptoResponse(
            coins=transformed_coins,
            total_count=len(transformed_coins),  # Items in current page
            last_updated=last_updated,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/cryptos/top/{limit}", response_model=CryptoResponse, summary="Get Top N Cryptocurrencies")
async def get_top_cryptos(limit: int = 100):
    """
    Fetch and return the top N cryptocurrencies from CoinGecko.
    
    Args:
        limit: Number of cryptocurrencies to return (max 1000)
    
    Returns:
        - List of top N cryptocurrencies
        - Total count of coins returned
        - Last updated timestamp
    """
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    
    try:
        logger.info(f"Fetching top {limit} cryptocurrencies...")
        raw_coins = fetch_coins_from_coingecko()
        
        if not raw_coins:
            raise HTTPException(status_code=404, detail="No cryptocurrency data found")
        
        # Limit to requested number
        limited_coins = raw_coins[:limit]
        
        # Transform data to our format
        transformed_coins = [transform_coin_data(coin) for coin in limited_coins]
        
        # Get the most recent last_updated timestamp
        last_updated = max(
            (coin.last_updated for coin in transformed_coins if coin.last_updated), 
            default=""
        )
        
        logger.info(f"Successfully fetched top {len(transformed_coins)} cryptocurrencies")
        
        return CryptoResponse(
            coins=transformed_coins,
            total_count=len(transformed_coins),
            last_updated=last_updated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    # For local debugging without using the command in the comment above
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


