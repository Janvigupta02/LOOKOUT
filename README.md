# MarketPulse - Smart Market Watchlist

**Know what changed. Know what matters.**

MarketPulse is an intelligent stock watchlist that helps you understand what has meaningfully changed since your last visit, not just what moved.

## Features

### 🎯 Core Features
- **Smart Change Detection**: AI-powered analysis of what's truly worth your attention
- **Attention Scoring**: 0-100 score based on price movement, volume anomalies, and market events
- **"What Did I Miss?"**: Dashboard showing meaningful changes since your last check
- **Severity Levels**: 
  - 🔴 Needs Attention (score 81-100)
  - 🟠 Significant (score 61-80)
  - 🟡 Worth Watching (score 31-60)
  - 🟢 Normal (score 0-30)

### 📊 Market Data
- **Real-time Quotes**: Alpha Vantage API integration with demo fallback
- **Stock Search**: Find and add stocks to your watchlist
- **Historical Tracking**: Price and volume snapshots over time
- **Market Events**: News and announcements that impact your stocks

### 🧠 Intelligence
- **Change Detection Service**: Analyzes price, volume, and event data
- **Explanation Service**: Generates human-readable explanations
- **User Checkpoints**: Tracks "last checked" state for each stock
- **Batch Summaries**: High-level overview of all watchlist changes

## Tech Stack

**Backend:**
- FastAPI (Python 3.13)
- SQLAlchemy + SQLite
- Alpha Vantage API for market data
- Pydantic for validation

**Frontend:**
- Single-page HTML/JavaScript
- Tailwind CSS for styling
- Vanilla JS (no build tools required)

## Setup Instructions

### 1. Prerequisites
- Python 3.10+ (tested on 3.13)
- pip

### 2. Clone & Install

```bash
cd marketpulse/backend
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp ../.env.example .env
```

**For Demo Mode (no API key required):**
```env
DEMO_MODE=true
ALPHA_VANTAGE_API_KEY=demo
DATABASE_URL=sqlite:///./marketpulse.db
```

**For Real Market Data:**

1. Get free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Update `.env`:

```env
DEMO_MODE=false
ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
DATABASE_URL=sqlite:///./marketpulse.db
```

### 4. Initialize Database

```bash
python -c "import sys; sys.path.insert(0, '.'); from utils.seed_data import seed_database; seed_database()"
```

This creates:
- Demo user (email: `demo@marketpulse.com`)
- Sample stocks (NVDA, AAPL, TSLA, AMZN)
- Historical data for meaningful change detection

### 5. Run the Server

```bash
python main.py
```

Server will start on `http://localhost:8000`

### 6. Access the App

Open your browser and go to:
```
http://localhost:8000
```

## API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

**Watchlist:**
- `GET /api/watchlist` - Get user's watchlist
- `POST /api/watchlist` - Add stock to watchlist
- `DELETE /api/watchlist/{ticker}` - Remove stock

**Dashboard:**
- `GET /api/dashboard` - Get "What Did I Miss?" summary

**Stocks:**
- `GET /api/stocks/search?q={query}` - Search stocks
- `GET /api/stocks/{ticker}` - Get stock details

**Checkpoints:**
- `POST /api/checkpoint` - Update "last checked" state

## Architecture Decisions

### What Counts as "Meaningful Change"?

**Attention Score (0-100):**
- 40% - Price movement
- 25% - Volume anomalies
- 20% - News/market events
- 15% - Other signals (52-week high/low, etc.)

**Thresholds:**
- Price: >2% (normal), >4% (worth watching), >7% (significant)
- Volume: >30% (moderate), >70% (high)

### State Persistence

**User Checkpoints:**
- Each user has a "last checked" timestamp per stock
- Stores last price/volume at checkpoint
- All changes calculated from this baseline
- Checkpoint updates on explicit user action

**Stock Snapshots:**
- Historical price/volume data stored
- Enables trend analysis
- Supports "rewind" to any point

### Data Freshness

**Demo Mode:**
- Simulated realistic data
- Deterministic for testing
- No rate limits

**Live Mode:**
- Alpha Vantage free tier: 5 calls/min
- 12-second delay between requests
- Automatic fallback to demo on errors

### Scalability Considerations

**Current (MVP):**
- SQLite for simplicity
- Synchronous API calls
- Single-user optimized

**Future (Production):**
- PostgreSQL for multi-user
- Background jobs for data fetching (Celery)
- Redis for caching quotes
- WebSocket for real-time updates
- Rate limiting per user

## Demo Scenarios

The seeded database includes 4 scenarios:

1. **NVDA (Needs Attention)**: +8.4% with high volume & positive news
2. **TSLA (Significant)**: -4.8% with negative delivery news
3. **AMZN (Worth Watching)**: +6.3% with AWS expansion news
4. **AAPL (Normal)**: +1.1% with minimal changes

## Limitations

- **Free API**: Alpha Vantage limits to 5 calls/min (free tier)
- **No Auth**: Single demo user (implement JWT for production)
- **No Real-time**: Polling-based (consider WebSockets)
- **Single Instance**: No distributed architecture yet

## Future Enhancements

- [ ] AI-powered explanations (Gemini/Groq integration)
- [ ] Real-time WebSocket updates
- [ ] Advanced pattern detection (technical indicators)
- [ ] Portfolio tracking & performance
- [ ] Email/SMS alerts for high-priority changes
- [ ] Mobile app (React Native)
- [ ] Social features (share watchlists)

## License

MIT

## Support

For issues or questions, open a GitHub issue.
