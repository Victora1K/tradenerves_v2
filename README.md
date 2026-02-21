# 📈 Tradenerves

A full-stack web application for analyzing candlestick pattern sequences in stock market data. Built with React, Flask, and SQLite, featuring real-time chart visualization, pattern detection, and simulated trading capabilities.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![React](https://img.shields.io/badge/react-18.3-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## 🌟 Features

### Pattern Analysis
- **3-Candle Sequence Detection** - Identify specific candlestick patterns (green, hammer, doji, red_doji, etc.)
- **Visual Sequence Markers** - Highlighted pattern indicators on interactive charts
- **Random Match Selection** - Explore different pattern occurrences across multiple symbols
- **Configurable Lookback/Forward Bars** - Customize chart window and playback range

### Chart Visualization
- **Interactive Candlestick Charts** - Powered by Plotly.js
- **Volume Analysis** - Synchronized volume bars below price chart
- **Playback Animation** - Step-by-step candle reveal for pattern analysis
- **Mobile Responsive** - Optimized for desktop, tablet, and mobile devices

### Trading Simulation
- **Paper Trading** - Simulate long/short positions with customizable leverage
- **Real-time P&L Tracking** - Monitor unrealized and realized profits
- **Pattern Performance** - Track performance by specific patterns
- **Position Management** - Buy, sell, and close positions

### Technical Stack
- **Frontend:** React 18, Plotly.js, Lucide Icons, Framer Motion
- **Backend:** Flask (Python 3.11), Gunicorn
- **Database:** SQLite with optimized pattern indexing
- **Deployment:** Docker & Docker Compose

---

## 🚀 Quick Start

### Prerequisites

- **Docker** (20.10+) and **Docker Compose** (2.0+) - [Install Docker](https://docs.docker.com/get-docker/)
- OR for local development: **Python 3.11+** and **Node.js 18+**

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/Victoralk/tradenerves_v2.git
cd tradenerves_v2

# Build and start containers
docker-compose build
docker-compose up -d

# Access application
# Frontend: http://localhost
# Backend: http://localhost:5000/api/health
```

**That's it!** See [`DOCKER_QUICKSTART.md`](DOCKER_QUICKSTART.md) for more details.

### Option 2: Local Development

**Backend:**
```bash
cd tradenerves-backend/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database and build patterns
python init_db.py
python data/fetch_data.py  # Fetch stock data (requires API key)
python build_patterns.py   # Build pattern tables (~5-10 min)

# Run Flask server
python app.py  # Runs on http://localhost:5000
```

**Frontend:**
```bash
cd tradenerves-frontend/webfront

# Install dependencies
corepack enable
yarn install

# Start development server
yarn start  # Runs on http://localhost:3000
```

---

## 📊 Database Setup

The application requires a populated `stocks.db` with pattern data:

### 1. Initialize Database
```bash
cd tradenerves-backend/backend
python init_db.py
```

### 2. Fetch Stock Data
```bash
python data/fetch_data.py
```
*Note: Requires API key from Polygon.io or similar provider*

### 3. Build Pattern Tables
```bash
python build_patterns.py
```
This creates:
- `pattern_occurrences` - Single candle patterns
- `pattern_sequences` - 3-candle sequences
- Indexes for fast lookups

**Expected patterns:** green, hammer, doji, red_doji, red, green_any, and custom sequences

---

## 🐳 Docker Deployment

Complete deployment guide: [`DOCKER_DEPLOYMENT.md`](DOCKER_DEPLOYMENT.md)

### Basic Commands

```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build && docker-compose up -d
```

### Production Deployment (AWS EC2)

See [`DOCKER_DEPLOYMENT.md`](DOCKER_DEPLOYMENT.md) for:
- EC2 instance setup
- SSL/HTTPS configuration
- Domain setup with Route 53
- Health monitoring
- Database backups

---

## 🏗️ Project Structure

```
Tradenerves/
├── docker-compose.yml              # Container orchestration
├── .gitignore                      # Git ignore rules
│
├── tradenerves-backend/
│   ├── Dockerfile                  # Backend container config
│   ├── .dockerignore
│   └── backend/
│       ├── app.py                  # Flask application
│       ├── requirements.txt        # Python dependencies
│       ├── routes/
│       │   └── optimized_patterns.py  # V2 API endpoints
│       ├── data/
│       │   ├── fetch_data.py       # Data fetching
│       │   ├── detect_patterns.py  # Pattern detection
│       │   └── precompute_sequences.py
│       ├── db/
│       │   └── stocks.db           # SQLite database (gitignored)
│       ├── init_db.py              # Database initialization
│       └── build_patterns.py       # Pattern table builder
│
└── tradenerves-frontend/
    ├── Dockerfile                  # Frontend container config
    ├── nginx.conf                  # Nginx reverse proxy
    ├── .dockerignore
    └── webfront/
        ├── package.json            # Node dependencies
        ├── src/
        │   ├── components/
        │   │   ├── Dashboard.js    # Main UI component
        │   │   ├── ui/             # Reusable UI components
        │   │   └── PatternsInfo.js
        │   ├── services/
        │   │   ├── api.js          # API client
        │   │   └── patternApi.js   # Pattern API methods
        │   ├── hooks/
        │   │   └── usePlayback.js  # Chart playback logic
        │   └── context/
        │       └── TradingContext.js  # Trading state management
        └── public/
```

---

## 🔌 API Endpoints

### V2 Optimized API

**Pattern Matches:**
```
GET /api/v2/patterns/matches
Parameters:
  - pattern: Pattern key or sequence (e.g., "green,hammer,doji")
  - symbol: Stock symbol (default: "any" - auto-select)
  - timeframe: 1D (only daily supported)
  - limit: Max results (default: 100)
```

**OHLCV Data with Lookback:**
```
GET /api/v2/data/with-lookback
Parameters:
  - symbol: Stock symbol
  - date: Anchor date (YYYY-MM-DD)
  - timeframe: 1D
  - lookback: Bars before date (default: 50)
  - forward: Bars after date (default: 20)
```

**Available Patterns:**
```
GET /api/v2/patterns/available
```

**Health Check:**
```
GET /api/health
```

---

## 🛠️ Configuration

### Backend Configuration

**Supported Symbols:** SPY, QQQ, AAPL, MSFT, NVDA, TSLA, GOOGL, AMZN, META, NFLX, AMD, JPM, V

**Timeframes:** Daily (1D) - Intraday support available but disabled in frontend

**Pattern Types:**
- Single candles: `green`, `hammer`, `doji`, `red_doji`, `red`, `green_any`
- Sequences: Comma-separated (e.g., `green,hammer,red_doji`)

### Frontend Configuration

**Environment Variables (optional):**
```bash
REACT_APP_API_URL=http://localhost:5000
```

**Chart Settings:**
- Lookback bars: 10 (configurable in Dashboard.js)
- Forward bars: 100 (configurable in Dashboard.js)
- Playback speed: Adjustable via UI

---

## 📱 Mobile Responsiveness

The frontend is fully responsive with breakpoints at:
- **Desktop:** 992px+
- **Tablet:** 768px - 991px
- **Mobile:** < 768px

Features:
- Stacked vertical layout on mobile
- Touch-friendly buttons (44px min height)
- Full-width controls
- Optimized chart sizing

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Plotly.js** - Interactive charting
- **Lucide Icons** - Beautiful icon set
- **Polygon.io** - Stock market data API
- **Flask** - Python web framework
- **React** - UI library

---

## 💰 Support Development

If you find this project helpful, consider supporting development:

**Bitcoin (BTC):** `0x73B61c903Cab90D5C251E58FEa6D90cC3d006a68`

---

## 📞 Contact

**Project Link:** [https://github.com/Victoralk/tradenerves_v2](https://github.com/Victoralk/tradenerves_v2)

---

## 🐛 Known Issues

- Intraday timeframes (5m, 10m, 15m, 1h) disabled - daily data only
- Pattern detection requires full database rebuild when adding new symbols
- Playback animation may lag on large datasets (>1000 bars)

---

## 🗺️ Roadmap

- [ ] Real-time data streaming
- [ ] More pattern types (head & shoulders, cup & handle, etc.)
- [ ] Multi-timeframe support
- [ ] Export/import trading history
- [ ] Advanced backtesting metrics
- [ ] Machine learning pattern predictions
- [ ] User authentication and saved portfolios

---

**Built with ❤️ for traders and developers**

*Disclaimer: This application is for educational and research purposes only. Not financial advice. Trade at your own risk.*
