# ✈️ Flight Search App - Scalable API-Based Solution

A modern, scalable flight search application built with FastAPI and Amadeus API.

## 🚀 Quick Start

### 1. Get Amadeus API Key (FREE)
1. Go to: https://developers.amadeus.com/
2. Click "Sign Up" (free account)
3. Create a new app
4. Copy your **API Key** and **API Secret**

### 2. Setup Environment
```bash
cd flight-search-app
cp .env.example .env
# Edit .env with your Amadeus credentials
```

### 3. Install & Run
```bash
pip install -r requirements.txt
python main.py
```

Visit: http://localhost:8030

## 🏗️ Architecture

```
flight-search-app/
├── app/
│   ├── api/           # REST API endpoints
│   ├── core/          # Configuration & security
│   ├── models/        # Pydantic models
│   ├── services/      # Business logic (Amadeus, caching)
│   └── utils/         # Helper functions
├── frontend/          # Modern web UI
├── tests/            # Test suite
└── main.py           # FastAPI app entry point
```

## 🎯 Features

- ✅ Real-time flight search (Amadeus API)
- ✅ Modern web interface
- ✅ REST API for integration
- ✅ Caching for performance
- ✅ Error handling & monitoring
- ✅ Scalable architecture

## 📊 API Endpoints

- `GET /` - Web interface
- `POST /api/search` - Search flights
- `GET /api/airports` - Get airport codes
- `GET /api/health` - Health check

## 🔧 Configuration

See `.env.example` for all configuration options.

---

**Built with:** FastAPI, Amadeus API, React, TypeScript
