# Crypto Analytics & Sentiment Analysis Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Flutter](https://img.shields.io/badge/App-Flutter-02569B)](https://flutter.dev/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)

A comprehensive full-stack application combining cryptocurrency market data with sentiment analysis capabilities. Built with FastAPI backend and Flutter mobile app.

## 🚀 Features

### Backend (FastAPI + SQLModel)
- **Cryptocurrency API**: Real-time crypto data from CoinGecko
- **Sentiment Analysis**: Multi-language text analysis (Persian & English)
- **Article Management**: Store and analyze news articles
- **Chat Bot**: Simple conversational interface
- **Rate Limiting**: Robust API handling with retry logic

### Flutter App
- **Crypto Dashboard**: Browse cryptocurrencies with pagination
- **Real-time Data**: Live price updates and market information
- **Interactive UI**: Modern Material Design 3 interface
- **Speech-to-Text**: Voice input capabilities
- **Settings**: Configurable backend URLs and demo mode

## 📁 Project Structure

```
├── backend/                 # FastAPI backend server
│   ├── main.py             # Main API server with crypto & sentiment endpoints
│   ├── rule_sentiment.py   # Persian sentiment analysis rules
│   ├── rule_sentiment_en.py # English sentiment analysis rules
│   ├── requirements.txt    # Python dependencies
│   └── tests/              # API tests
├── flutter_app/            # Flutter mobile application
│   ├── lib/
│   │   ├── pages/          # App screens (crypto, settings, speech-to-text)
│   │   ├── models/         # Data models (crypto, articles, chat)
│   │   ├── services/       # API services
│   │   └── providers/      # State management
│   └── assets/             # Sample data and resources
├── scripts/                # Data collection and processing scripts
└── data/                   # Raw data storage
```

## 🛠️ Installation & Setup

### Backend Setup

**Prerequisites**: Python 3.10+

1. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

2. Run the server:
```bash
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`

### Flutter App Setup

**Prerequisites**: Flutter SDK installed

1. Install dependencies:
```bash
cd flutter_app
flutter pub get
```

2. Run the app:
```bash
flutter run
```

## 📡 API Endpoints

### Cryptocurrency Endpoints

#### Get Paginated Cryptocurrencies
```bash
GET /cryptos?page=1&per_page=10
```

#### Get Top N Cryptocurrencies
```bash
GET /cryptos/top/100
```

**Example Response:**
```json
{
  "coins": [
    {
      "rank": 1,
      "symbol": "BTC",
      "id": "bitcoin",
      "name": "Bitcoin",
      "price_usd": 45000.50,
      "market_cap_usd": 850000000000,
      "change_24h_pct": 2.5,
      "total_volume_usd": 25000000000,
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 10,
  "last_updated": "2024-01-15T10:30:00Z",
  "page": 1,
  "per_page": 10,
  "total_pages": 100,
  "has_next": true,
  "has_prev": false
}
```

### Sentiment Analysis Endpoints

#### Analyze Text Sentiment
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"text":"This is a great day! 😊"}'
```

#### Ingest Article
```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '{"title":"Crypto News","content":"Bitcoin reaches new all-time high!"}'
```

#### List Articles
```bash
curl http://127.0.0.1:8000/articles
```

#### Chat Bot
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Hello, how are you?"}'
```

## 🧪 Testing

Run backend tests:
```bash
pytest backend/tests/
```

## 🎯 Key Features

### Cryptocurrency Data
- **Real-time Prices**: Live data from CoinGecko API
- **Market Metrics**: Market cap, volume, 24h change
- **Pagination**: Efficient data loading with pagination
- **Rate Limiting**: Robust handling of API rate limits
- **Error Handling**: Comprehensive error management

### Sentiment Analysis
- **Multi-language**: Persian and English support
- **Rule-based**: Custom sentiment analysis rules
- **Translation**: Automatic translation for non-English text
- **Persistence**: Store analysis results in database

### Flutter App Features
- **Modern UI**: Material Design 3 with teal color scheme
- **Responsive Design**: Works on phones and tablets
- **State Management**: Provider pattern for app state
- **Error Handling**: User-friendly error messages
- **Connectivity Testing**: Built-in API connectivity tests

## 🔧 Configuration

### Backend Configuration
- **Database**: SQLite (configurable in `main.py`)
- **API Rate Limits**: Configurable delays and retry logic
- **Language Detection**: Deterministic language detection

### Flutter Configuration
- **Backend URL**: Configurable in settings
- **Demo Mode**: Toggle for offline testing
- **Platform-specific URLs**: Automatic Android emulator detection

## 🚀 Deployment

### Docker Support
```bash
docker-compose up
```

To serve the Flutter web build via Nginx (after running `flutter build web`):

```bash
cd flutter_app
flutter build web
cd ..
docker-compose up -d web
```

### Production Considerations
- Configure proper database (PostgreSQL recommended)
- Set up proper API rate limiting
- Implement authentication if needed
- Configure CORS for production domains

### Releases
- Use semantic versioning for tags/releases (e.g., v0.1.0)
- Draft release notes summarizing changes (features, fixes, docs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Dev setup

Install pre-commit hooks (format/lint Python and Dart):

```bash
pip install pre-commit
pre-commit install
```

## 📄 License

This project is open source and available under the MIT License.
