# Trading Scanner — MT5 Signal Bot + Streamlit Dashboard

A professional **Forex & Gold trading scanner** built in Python that connects to **MetaTrader 5**, detects high-probability setups using Smart Money Concepts (SMC), scores them, and sends **progressive Telegram alerts** with chart screenshots.

Designed as Phase 1 of a full **Trading Operating System** — no auto-execution, full manual control.

---

## Features

### Market Scanner
- Connects to MetaTrader 5 via the official Python API
- Scans **6 instruments** simultaneously: XAUUSD, EURUSD, GBPUSD, USDJPY, GBPJPY, EURJPY
- Multi-timeframe analysis: H4 bias → H1 structure → M15 entry
- Runs on a configurable interval (default 60s)

### Strategy Logic (Smart Money Concepts)
| Condition | Description |
|-----------|-------------|
| HTF Bias | Bullish/bearish trend via EMA20/EMA50 on H4 |
| Market Structure | Swing highs/lows across timeframes |
| Break of Structure (BOS) | Price closes beyond last confirmed swing |
| Liquidity Sweep | Wick past structural level, body closes back inside |
| Fair Value Gap (FVG) | 3-candle imbalance detection, tracks filled/unfilled |
| Retest | Price returning to FVG or broken structure |
| Rejection Candle | Hammer, shooting star, bullish/bearish engulfing |
| Session Filter | London, New York, London/NY overlap, Asian |
| Risk-to-Reward | Auto-calculated entry, SL, TP1 (2R), TP2 (3R) |
| **News Filter** | Blocks alerts 30m before / 15m after HIGH-impact events (ForexFactory) |

### Setup Scoring Engine
Each setup is dynamically scored (max 14 points) and graded:

| Grade | Min Score | Description |
|-------|-----------|-------------|
| 🥉 Standard | 4 | Basic confluence |
| 🥈 A | 7 | Good setup |
| 🥇 A+ | 10 | High-probability |
| 💎 Elite | 12 | All conditions confirmed |

### Telegram Alerts
Progressive staged alerts sent with chart screenshots:

- 🔍 Setup Developing
- ⚡ Entry Zone Approaching
- ✅ 5-Min / 15-Min Confirmation
- 🎯 High-Confidence Setup

Each alert includes grade, score bar, bias, session, entry/SL/TP levels.

### Risk Management Constitution
Automatically suspends alerts when limits are breached:
- Max % risk per trade (used for lot size calculation)
- Daily drawdown limit
- Weekly drawdown limit
- Max consecutive losses

### Trade Journal & Database
SQLite database storing:
- Setups detected (symbol, grade, score, levels, chart path)
- Trades (entry, SL, TP, outcome, RR achieved, notes)
- Journal entries (daily review responses)
- Risk log (equity, drawdown history)

### News Filter
- Fetches the **ForexFactory weekly calendar** (public JSON endpoint, no API key needed)
- Caches events locally for 1 hour, refreshes automatically
- Maps each symbol to its currencies (e.g. GBPJPY → GBP + JPY)
- Suppresses scanner alerts during the blackout window around HIGH-impact events
- Sends a Telegram notification when an alert is blocked (once per symbol, with cooldown)
- Window is fully configurable via `.env`

### Streamlit Dashboard
Seven-page dashboard:

| Page | Contents |
|------|----------|
| Dashboard | Today's stats, recent setups, next high-impact event countdown, equity trend |
| **Economic Calendar** | Live ForexFactory events, countdown timer, impact filter, timeline chart, scanner blackout indicator |
| Active Setups | Filterable setup table with chart previews |
| Trade Journal | Log and close trades |
| Analytics | Win rate, RR distribution, cumulative RR curve, performance by grade/symbol/session |
| Daily Review | End-of-day reflection form (stored for future AI coaching) |
| Risk Status | Drawdown tracker, consecutive loss chart, constitution rules |

---

## Project Structure

```
trading-scanner/
├── main.py                    # Scanner entry point (runs the loop)
├── config.py                  # All settings loaded from .env
├── scanner/
│   ├── mt5_connector.py       # MT5 connection and bar fetching
│   ├── market_analyzer.py     # Full SMC strategy logic
│   ├── scoring_engine.py      # Setup scoring and grading
│   ├── chart_generator.py     # Dark-theme candlestick charts (mplfinance)
│   └── news_filter.py         # ForexFactory calendar + blackout logic
├── alerts/
│   └── telegram_bot.py        # Telegram message and photo sending
├── risk/
│   └── risk_manager.py        # Constitution rules enforcement + lot sizing
├── database/
│   └── db_manager.py          # SQLite schema + all CRUD operations
├── dashboard/
│   └── app.py                 # Streamlit 7-page dashboard
├── requirements.txt
└── .env.example
```

---

## Setup

### Requirements
- **Windows** (MetaTrader5 Python package is Windows-only)
- MetaTrader 5 terminal installed and logged in
- Python 3.10+
- A Telegram bot (create via [@BotFather](https://t.me/BotFather))

### Install

```bash
git clone https://github.com/NadirAliOfficial/trading-scanner.git
cd trading-scanner
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
MT5_LOGIN=123456
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Server
```

### Run the Scanner

```bash
python main.py
```

### Run the Dashboard

```bash
streamlit run dashboard/app.py
```

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SCAN_INTERVAL` | `60` | Seconds between scans |
| `ALERT_COOLDOWN_MINUTES` | `60` | Min minutes between repeat alerts per symbol/grade |
| `MAX_RISK_PER_TRADE` | `1.0` | % of account per trade |
| `MAX_DAILY_DRAWDOWN` | `3.0` | Daily DD % limit |
| `MAX_WEEKLY_DRAWDOWN` | `6.0` | Weekly DD % limit |
| `MAX_CONSECUTIVE_LOSSES` | `3` | Losses before scanner pauses |
| `SCORE_STANDARD` | `4` | Min score for Standard alert |
| `SCORE_A` | `7` | Min score for A alert |
| `SCORE_A_PLUS` | `10` | Min score for A+ alert |
| `SCORE_ELITE` | `12` | Min score for Elite alert |
| `NEWS_FILTER_ENABLED` | `true` | Enable/disable news blackout |
| `NEWS_BLOCK_MINUTES_BEFORE` | `30` | Minutes before event to block alerts |
| `NEWS_BLOCK_MINUTES_AFTER` | `15` | Minutes after event to resume alerts |

---

## Roadmap
- [ ] AI coaching feedback based on journal entries
- [ ] Multi-broker support
- [ ] Webhook-based Telegram bot for journal commands
- [ ] Machine learning setup quality predictor

---

## Disclaimer

This tool is for **decision support only**. It does not place trades automatically. All execution is manual. Past performance of any strategy does not guarantee future results. Trade responsibly.

---

## License

MIT
