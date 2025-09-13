"""Main FastAPI application for the unified API.

This is the entry point for the unified API that combines sentiment analysis
and cryptocurrency functionality. The application is organized into modular
services for better maintainability and readability.
"""

import logging
from typing import Dict, List

from fastapi import Depends, FastAPI, HTTPException, Response
from sqlmodel import Session

# Import local modules
from article_service import (
    create_article,
    get_all_articles,
    ingest_from_json_directory,
)
from chat_service import process_chat_message
from crypto_service import (
    fetch_coins_from_coingecko,
    fetch_coins_from_coingecko_paginated,
    transform_coin_data,
)
from database import create_db_and_tables, get_session
from models import (
    AnalyzeRequest,
    Article,
    ArticleCreate,
    ChatRequest,
    CryptoResponse,
)
from sentiment_service import analyze_text_sentiment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# How to run the server (development):
#   uvicorn main:app --reload

# Initialize FastAPI application
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
def ingest_article_endpoint(payload: ArticleCreate, session: Session = Depends(get_session)) -> Article:
    """Create a new article."""
    return create_article(payload, session)


@app.get("/articles", response_model=List[Article])
def list_articles(session: Session = Depends(get_session)) -> List[Article]:
    """Get all articles ordered by creation date (newest first)."""
    return get_all_articles(session)


@app.post("/analyze")
def analyze_endpoint(payload: AnalyzeRequest, session: Session = Depends(get_session)):
    """Analyze text sentiment and return detailed results."""
    return analyze_text_sentiment(payload.text, session)


@app.post("/ingest_feeds")
def ingest_from_raw_directory_endpoint(session: Session = Depends(get_session)) -> Dict[str, object]:
    """Scan data/raw/*.json and ingest new articles, analyzing each only once by title."""
    return ingest_from_json_directory("data/raw", session)


@app.post("/chat")
def chat_with_bot(request: ChatRequest) -> Dict[str, str]:
    """Simple chatbot endpoint that provides contextual responses."""
    return process_chat_message(request.message)


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