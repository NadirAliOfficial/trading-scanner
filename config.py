import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

MT5_LOGIN = int(os.getenv("MT5_LOGIN", "0"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")

SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "EURJPY"]

SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "60"))

MAX_RISK_PER_TRADE = float(os.getenv("MAX_RISK_PER_TRADE", "1.0"))
MAX_DAILY_DRAWDOWN = float(os.getenv("MAX_DAILY_DRAWDOWN", "3.0"))
MAX_WEEKLY_DRAWDOWN = float(os.getenv("MAX_WEEKLY_DRAWDOWN", "6.0"))
MAX_CONSECUTIVE_LOSSES = int(os.getenv("MAX_CONSECUTIVE_LOSSES", "3"))

SCORE_STANDARD = 4
SCORE_A = 7
SCORE_A_PLUS = 10
SCORE_ELITE = 12

HTF = "H4"
MTF = "H1"
LTF = "M15"

DB_PATH = os.getenv("DB_PATH", "trading_scanner.db")
SCREENSHOTS_DIR = "screenshots"
ALERT_COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MINUTES", "60"))
