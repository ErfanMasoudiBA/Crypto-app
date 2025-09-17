"""
Cryptocurrency API service module.

This module handles all cryptocurrency-related functionality including
fetching data from CoinGecko API, rate limiting, data transformation,
and error handling.
"""

import logging
import time
import os
from typing import Any, Dict, List, Tuple

import requests
from fastapi import HTTPException

from models import CryptoCoin

# Configure logging
logger = logging.getLogger(__name__)

# API Constants (can be overridden with environment variables)
COINGECKO_MARKETS = os.getenv("COINGECKO_MARKETS", "https://api.coingecko.com/api/v3/coins/markets")
PER_PAGE = int(os.getenv("COINGECKO_PER_PAGE", "250"))
MAX_COINS = int(os.getenv("COINGECKO_MAX_COINS", "1000"))
RETRY_DELAY = int(os.getenv("COINGECKO_RETRY_DELAY", "15"))
REQUEST_DELAY = int(os.getenv("COINGECKO_REQUEST_DELAY", "5"))
CRYPTO_CACHE_TTL = int(os.getenv("CRYPTO_CACHE_TTL", "60"))  # seconds

# Simple in-memory cache: key -> (timestamp, value)
_cache: Dict[str, Tuple[float, Any]] = {}

def _cache_get(key: str):
    now = time.time()
    entry = _cache.get(key)
    if not entry:
        return None
    ts, value = entry
    if now - ts > CRYPTO_CACHE_TTL:
        _cache.pop(key, None)
        return None
    return value

def _cache_set(key: str, value: Any):
    _cache[key] = (time.time(), value)


def fetch_coins_from_coingecko() -> List[Dict[str, Any]]:
    """
    Fetch top 1000 cryptocurrencies from CoinGecko API with rate limiting.
    
    Returns:
        List[Dict[str, Any]]: List of cryptocurrency data from CoinGecko API
        
    Raises:
        HTTPException: If API request fails or rate limit is exceeded
    """
    cache_key = f"top:{MAX_COINS}"
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.info("Serving top coins from cache")
        return cached

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
    
    _cache_set(cache_key, all_coins)
    return all_coins


def fetch_coins_from_coingecko_paginated(page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch a specific page of cryptocurrencies from CoinGecko API with rate limiting.
    
    Args:
        page: Page number (minimum: 1)
        per_page: Number of items per page (range: 1-250)
        
    Returns:
        List[Dict[str, Any]]: List of cryptocurrency data for the requested page
        
    Raises:
        HTTPException: If validation fails or API request fails
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
    cache_key = f"page:{page}:per:{per_page}"
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.info("Serving paginated coins from cache")
        return cached
    
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
    _cache_set(cache_key, data)
    return data


def transform_coin_data(coin_data: Dict[str, Any]) -> CryptoCoin:
    """
    Transform raw CoinGecko data to our API format.
    
    Args:
        coin_data: Raw cryptocurrency data from CoinGecko API
        
    Returns:
        CryptoCoin: Transformed cryptocurrency data model
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
        last_updated=coin_data.get("last_updated"),
        image_url=coin_data.get("image")
    )