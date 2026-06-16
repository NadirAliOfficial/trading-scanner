import pandas as pd
import sys

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

import config

TF_MAP = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 16385,
    "H4": 16388,
    "D1": 16408,
    "W1": 32769,
}

if MT5_AVAILABLE:
    TF_MAP = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
    }


def connect():
    if not MT5_AVAILABLE:
        raise RuntimeError("MetaTrader5 package not installed. Install on Windows: pip install MetaTrader5")
    if not mt5.initialize(
        login=config.MT5_LOGIN,
        password=config.MT5_PASSWORD,
        server=config.MT5_SERVER,
    ):
        raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")
    return True


def disconnect():
    if MT5_AVAILABLE:
        mt5.shutdown()


def get_bars(symbol, timeframe, count=200):
    if not MT5_AVAILABLE:
        return None
    tf = TF_MAP.get(timeframe, mt5.TIMEFRAME_H1)
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
    if rates is None:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    df.rename(columns={
        "open": "Open", "high": "High",
        "low": "Low", "close": "Close",
        "tick_volume": "Volume",
    }, inplace=True)
    return df[["Open", "High", "Low", "Close", "Volume"]]


def get_account_info():
    if not MT5_AVAILABLE:
        return {}
    info = mt5.account_info()
    if info is None:
        return {}
    return {
        "balance": info.balance,
        "equity": info.equity,
        "profit": info.profit,
        "margin": info.margin,
        "free_margin": info.margin_free,
        "leverage": info.leverage,
        "currency": info.currency,
        "login": info.login,
        "server": info.server,
    }


def get_symbol_info(symbol):
    if not MT5_AVAILABLE:
        return {}
    info = mt5.symbol_info(symbol)
    if info is None:
        return {}
    return {
        "digits": info.digits,
        "point": info.point,
        "trade_contract_size": info.trade_contract_size,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
    }
