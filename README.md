# TradeCopy

A trade copying system that reads signals from Telegram and FX Blue, executes them on MetaTrader 5, with multi-user support (50+ accounts) and a web app for configuration.

## Features

- **Telegram Signal Parsing**: Automatically parse trading signals from Telegram channels using regex patterns
- **FX Blue Integration**: Receive and send signals via FX Blue trade mirror
- **Multi-Account Support**: Manage 50+ MT5 accounts with efficient connection pooling
- **Multiple Take Profits**: Split orders for multiple TP levels (equal, front-weighted, back-weighted, custom)
- **Real-time Updates**: WebSocket-based live updates for signals and trades
- **Web Dashboard**: React-based UI for configuration and monitoring
- **Multi-Tenant**: Row-Level Security for data isolation between users

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   TELEGRAM      │     │   FX BLUE       │     │   WEB APP       │
│   (Telethon)    │     │  (Bridge EA)    │     │   (React)       │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     FASTAPI BACKEND     │
                    │   (REST + WebSocket)    │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────▼────────┐   ┌─────────▼─────────┐   ┌────────▼────────┐
│  SIGNAL PARSER  │   │      REDIS        │   │   POSTGRESQL    │
│    (Regex)      │   │  (Queue/Cache)    │   │  (Multi-tenant) │
└────────┬────────┘   └─────────┬─────────┘   └─────────────────┘
         │                      │
         └──────────┬───────────┘
                    │
         ┌──────────▼──────────┐
         │   CELERY WORKERS    │
         │  (Trade Execution)  │
         └──────────┬──────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌───▼───┐       ┌───▼───┐       ┌───▼───┐
│ MT5-1 │       │ MT5-2 │       │ MT5-N │
└───────┘       └───────┘       └───────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ / FastAPI |
| Database | PostgreSQL 15+ (Row-Level Security) |
| Cache/Queue | Redis 7+ |
| Task Queue | Celery |
| Telegram | Telethon |
| MT5 | MetaTrader5 Python API |
| Frontend | React + TypeScript + Tailwind |
| Containerization | Docker Desktop for Windows |

## Quick Start

### Prerequisites

- Docker Desktop for Windows (with WSL2)
- MetaTrader 5 installed
- Telegram API credentials (from my.telegram.org)

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repo-url>
cd tradeCopy

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
```

### 2. Start Services

```bash
cd docker
docker-compose up -d
```

This starts:
- PostgreSQL database
- Redis cache/queue
- FastAPI backend (http://localhost:8000)
- Celery workers
- Telegram listener
- React frontend (http://localhost:3000)

### 3. Run Database Migrations

```bash
docker-compose exec api alembic upgrade head
```

### 4. Access the App

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## Development

### Backend Only

```bash
cd backend
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

### Frontend Only

```bash
cd frontend
npm install
npm run dev
```

### Workers (on Windows host for MT5)

```bash
cd workers
pip install -r requirements.txt
celery -A workers.celery_app worker --loglevel=info
```

## FX Blue Setup

See [fxblue_bridge/README.md](fxblue_bridge/README.md) for FX Blue EA setup instructions.

## Signal Format Examples

The parser supports various signal formats:

```
BUY EURUSD @ 1.0850
SL: 1.0800
TP1: 1.0900
TP2: 1.0950
TP3: 1.1000
```

```
GOLD SELL
Entry: 2020 - 2025
Stop Loss: 2035
Take Profit 1: 2010
Take Profit 2: 2000
Take Profit 3: 1990
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/register` | Register new user |
| `POST /api/v1/auth/login` | Login |
| `GET /api/v1/channels` | List Telegram channels |
| `GET /api/v1/mt5-accounts` | List MT5 accounts |
| `GET /api/v1/subscriptions` | List channel-account subscriptions |
| `GET /api/v1/signals` | List parsed signals |
| `GET /api/v1/trades` | List executed trades |
| `WS /api/v1/ws/live` | WebSocket for real-time updates |

See http://localhost:8000/docs for full API documentation.

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT signing key |
| `FERNET_KEY` | Encryption key for MT5 passwords |
| `TELEGRAM_API_ID` | Telegram API ID |
| `TELEGRAM_API_HASH` | Telegram API hash |
| `TELEGRAM_SESSION_STRING` | Telegram session string |

### Subscription Settings

- **Lot Size**: Fixed lot size or auto from signal
- **Risk %**: Percentage of balance per trade
- **TP Strategy**: equal, front_weighted, back_weighted, single, custom
- **Symbol Mapping**: Map signal symbols to broker symbols

## Notes

- **Windows**: MT5 Python API only works on Windows. Run workers on Windows host.
- **Rate Limits**: Telegram has rate limits. The listener respects them automatically.
- **Broker Restrictions**: Some brokers don't allow API trading. Check with your broker.
- **Demo First**: Always test with demo accounts before live trading.

## License

MIT
