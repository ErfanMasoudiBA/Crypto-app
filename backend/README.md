# Unified API

A lightweight, modular FastAPI application that combines sentiment analysis and cryptocurrency data fetching. The application is built with clean code principles and follows modern Python development practices.

## Features

### Sentiment Analysis

- **Multilingual Support**: Text sentiment analysis with Persian and English support
- **Language Detection**: Automatic language detection and translation
- **Article Management**: Article ingestion, storage, and sentiment analysis
- **Interactive Chat**: Simple chatbot endpoint with contextual responses
- **Database Persistence**: All analyses are stored for future reference

### Cryptocurrency Data

- **Real-time Market Data**: Fetch top 1000 cryptocurrencies from CoinGecko API
- **Flexible Queries**: Get top N cryptocurrencies with customizable limits
- **Comprehensive Data**: Prices, market cap, volume, and 24h changes
- **Rate Limiting**: Built-in retry logic and request throttling
- **Error Handling**: Robust error handling for API failures

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the API

```bash
# Option 1: Using uvicorn directly
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Option 2: Using the run script
python run.py

# Option 3: Direct execution
python main.py
```

### 3. Access the API

- **API Documentation**: http://127.0.0.1:8000/docs (Interactive Swagger UI)
- **Alternative Docs**: http://127.0.0.1:8000/redoc (ReDoc)
- **Health Check**: http://127.0.0.1:8000/
- **API Status**: http://127.0.0.1:8000/ (Shows available endpoints)

## API Endpoints

### Sentiment Analysis Endpoints

- `POST /analyze` - Analyze text sentiment with language detection
  - **Input**: `{"text": "Your text here"}`
  - **Output**: Sentiment scores, detected language, and confidence
- `POST /ingest` - Create and store new articles
  - **Input**: `{"title": "Article title", "content": "Article content"}`
- `GET /articles` - Retrieve all stored articles (newest first)
- `POST /ingest_feeds` - Bulk ingest articles from JSON files in data/raw/
- `POST /chat` - Interactive chatbot endpoint
  - **Input**: `{"message": "Your message"}`
  - **Output**: Contextual bot response

### Cryptocurrency Endpoints

- `GET /cryptos?page=1&per_page=10` - Get paginated cryptocurrency data
  - **Parameters**: `page` (1+), `per_page` (1-250)
  - **Output**: Paginated list with metadata
- `GET /cryptos/top/{limit}` - Get top N cryptocurrencies by market cap
  - **Parameters**: `limit` (1-1000)
  - **Output**: List of top cryptocurrencies

### System Endpoints

- `GET /` - API status and available endpoints
- `GET /favicon.ico` - Favicon (returns 204 No Content)

## Database

The API uses **SQLite** for data persistence with the following features:

- **Automatic Setup**: Database file (`app.db`) created automatically on first run
- **Schema Management**: Tables created automatically using SQLModel
- **Data Models**:
  - `Article`: Stores article title, content, and creation timestamp
  - `Analysis`: Stores sentiment analysis results with scores and metadata

### Database Schema

```sql
-- Articles table
CREATE TABLE article (
    id INTEGER PRIMARY KEY,
    title VARCHAR NOT NULL,
    content VARCHAR NOT NULL,
    created_at DATETIME NOT NULL
);

-- Analysis table
CREATE TABLE analysis (
    id INTEGER PRIMARY KEY,
    text VARCHAR NOT NULL,
    label VARCHAR NOT NULL,
    positive REAL NOT NULL,
    negative REAL NOT NULL,
    neutral REAL NOT NULL,
    created_at DATETIME NOT NULL
);
```

## Project Structure

The application follows a modular architecture for better maintainability and scalability:

```
backend/
├── main.py              # FastAPI application entry point
├── models.py            # Data models (SQLModel & Pydantic)
├── database.py          # Database configuration & session management
├── crypto_service.py    # Cryptocurrency API service
├── sentiment_service.py # Sentiment analysis service
├── article_service.py   # Article management service
├── chat_service.py      # Chat/bot functionality
├── rule_sentiment.py    # Persian sentiment analysis rules
├── rule_sentiment_en.py # English sentiment analysis rules
├── requirements.txt     # Project dependencies
└── tests/              # Unit tests
```

### Module Responsibilities

- **main.py**: FastAPI application setup and route definitions
- **models.py**: All SQLModel and Pydantic model definitions
- **database.py**: Database engine configuration and session management
- **crypto_service.py**: CoinGecko API integration and cryptocurrency data handling
- **sentiment_service.py**: Text sentiment analysis and language processing
- **article_service.py**: Article ingestion, storage, and retrieval
- **chat_service.py**: Simple chatbot response generation
- **rule_sentiment\*.py**: Rule-based sentiment analysis for different languages

## Dependencies

- **FastAPI** - Modern web framework for building APIs
- **Uvicorn** - Lightning-fast ASGI server
- **SQLModel** - SQL databases in Python with type safety
- **Requests** - HTTP library for API calls
- **Langdetect** - Language detection library
- **Googletrans** - Google Translate API wrapper

## Development

### Code Quality

The project follows clean code principles:

- **Modular Architecture**: Separated concerns into focused modules
- **Type Safety**: Full type hints throughout the codebase
- **Error Handling**: Comprehensive error handling and logging
- **Documentation**: Detailed docstrings and comments
- **Testing**: Unit tests for core functionality

### Adding New Features

1. **Services**: Add new functionality to appropriate service modules
2. **Models**: Define new data models in `models.py`
3. **Endpoints**: Add new routes in `main.py`
4. **Tests**: Write tests in the `tests/` directory

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_api.py
```

## Configuration

### Environment Variables

The application can be configured using environment variables:

- `DATABASE_URL`: Custom database connection string (default: sqlite:///app.db)
- `LOG_LEVEL`: Logging level (default: INFO)
- `API_HOST`: Server host (default: 127.0.0.1)
- `API_PORT`: Server port (default: 8000)

### Rate Limiting

Cryptocurrency API calls include built-in rate limiting:

- **Retry Logic**: Exponential backoff on rate limit errors
- **Request Delay**: 5-second delay between requests
- **Max Retries**: 3 attempts per request

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`
2. **Database Errors**: Delete `app.db` file to recreate the database
3. **API Rate Limits**: CoinGecko API may rate limit requests; built-in retry logic handles this
4. **Translation Errors**: Google Translate may occasionally fail; the app falls back gracefully

### Logs

The application logs important events:

- Server startup and shutdown
- API requests and responses
- Database operations
- Error conditions and recoveries

## License

This project is open source and available under the [MIT License](LICENSE).
