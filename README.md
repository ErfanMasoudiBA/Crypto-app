# First Project

Structure:
- backend/
- flutter_app/
- scripts/
- data/
- models/

## Backend: FastAPI + SQLModel

Prerequisites: Python 3.10+

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Run the server (default on port 8000):

```bash
uvicorn backend.main:app --reload --port 8000
```

### Curl examples

Analyze arbitrary text:

```bash
curl -s -X POST http://127.0.0.1:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"text":"این یک روز عالی و دوست‌داشتنی است 😊"}' | jq
```

Ingest an article:

```bash
curl -s -X POST http://127.0.0.1:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '{"title":"نمونه خبر","content":"متن خبر بسیار جالب و عالی است."}' | jq
```

List articles:

```bash
curl -s http://127.0.0.1:8000/articles | jq
```

## Tests

Run tests with pytest:

```bash
pytest
```

## Flutter demo app

Prerequisites: Flutter SDK installed.

Install dependencies and run:

```bash
cd flutter_app
flutter pub get
flutter run
```

The app includes a Demo Mode that loads `assets/sample.json`. You can switch backend URL and demo mode in Settings.
