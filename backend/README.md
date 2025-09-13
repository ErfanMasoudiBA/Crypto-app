# Unified API

A lightweight FastAPI application that combines sentiment analysis and cryptocurrency data fetching.

## Features

### Sentiment Analysis
- Text sentiment analysis with Persian and English support
- Language detection and automatic translation
- Article ingestion and analysis
- Simple chatbot endpoint

### Cryptocurrency Data
- Fetch top 1000 cryptocurrencies from CoinGecko
- Get top N cryptocurrencies with customizable limit
- Real-time market data including prices, market cap, and volume

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the API:
```bash
# Option 1: Using uvicorn directly
uvicorn main:app --reload

# Option 2: Using the run script
python run.py
```

3. Access the API:
- API Documentation: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/

## API Endpoints

### Sentiment Analysis
- `POST /analyze` - Analyze text sentiment
- `POST /ingest` - Ingest articles
- `GET /articles` - List articles
- `POST /chat` - Simple chatbot

### Cryptocurrency
- `GET /cryptos` - Get top 1000 cryptocurrencies
- `GET /cryptos/top/{limit}` - Get top N cryptocurrencies

## Database

The API uses SQLite for data persistence. The database file (`app.db`) will be created automatically on first run.

## Dependencies

- FastAPI - Web framework
- Uvicorn - ASGI server
- SQLModel - Database ORM
- Requests - HTTP client
- Langdetect - Language detection
- Googletrans - Translation service
