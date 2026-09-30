# Global News Intelligence (GNI)

A local-first Global News Intelligence application designed to continuously collect news from legitimate sources, cluster articles describing the same real-world event, geolocate them with high precision, rank importance and confidence, and present them on an interactive world map.

## Core Abstraction

```
SOURCE → ARTICLE → EVENT → RANKING → GEOGRAPHIC VISUALIZATION
```

The system prioritizes **events**, not individual articles. For example, 100 articles reporting the same earthquake become **ONE EVENT** with 100 associated articles/sources.

## Architecture

* **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, MapLibre GL JS
* **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic
* **Database**: PostgreSQL 16 + PostGIS 3.4 (with automatic local SQLite fallback for development)
* **Message Broker / Cache**: Redis 7
* **Pipeline Workers**: Modular Python workers for collection, normalization, extraction, embeddings, clustering, and ranking
* **AI Provider Abstraction**: Local quantized models (GGUF/llama.cpp/ONNX/CPU fallback)

## Getting Started

### 1. Requirements
* Python 3.11+
* Node.js 20+
* Docker & Docker Compose (optional for local SQLite mode, required for full PostGIS containerized stack)

### 2. Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 3. Running with Docker Compose
```bash
docker compose up -d
```

### 4. Running Locally on Host (Without Docker)

#### Backend:
```bash
cd global-news-intelligence
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r apps/api/requirements.txt
alembic upgrade head
uvicorn apps.api.app.main:app --reload --port 8000
```

#### Frontend:
```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.
API Documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).
Health check is at [http://localhost:8000/health](http://localhost:8000/health).

## Testing
```bash
pytest apps/api/tests
```
