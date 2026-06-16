import requests
import config

STAGE_HEADERS = {
    "setup_developing": "🔍 SETUP DEVELOPING",
    "entry_zone": "⚡ ENTRY ZONE APPROACHING",
    "m5_confirmation": "✅ 5-MIN CONFIRMATION",
    "m15_confirmation": "✅ 15-MIN CONFIRMATION",
    "high_confidence": "🎯 HIGH-CONFIDENCE SETUP",
    "risk_violation": "🚨 RISK ALERT",
}

BIAS_EMOJI = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}


def _post(method, **kwargs):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{method}"
    try:
        r = requests.post(url, timeout=15, **kwargs)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[Telegram] {method} error: {e}")
        return False


def send_message(text):
    return _post("sendMessage", json={
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    })


def send_photo(photo_path, caption=""):
    with open(photo_path, "rb") as f:
        return _post("sendPhoto", data={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "caption": caption[:1024],
            "parse_mode": "HTML",
        }, files={"photo": f})


def format_alert(symbol, analysis, scoring, alert_stage="setup_developing"):
    from scanner.scoring_engine import GRADE_EMOJI
    bias = analysis.get("bias", "neutral")
    levels = analysis.get("levels") or {}
    conditions = analysis.get("conditions", [])
    session = analysis.get("session", "unknown").replace("_", " ").title()
    grade = scoring.get("grade", "Standard")
    score = scoring.get("score", 0)
    max_score = scoring.get("max_score", 14)
    breakdown = scoring.get("breakdown", [])

    header = STAGE_HEADERS.get(alert_stage, "📊 SIGNAL ALERT")
    grade_emoji = GRADE_EMOJI.get(grade, "📊")
    bias_emoji = BIAS_EMOJI.get(bias, "⚪")

    progress_filled = int((score / max_score) * 10)
    progress_bar = "█" * progress_filled + "░" * (10 - progress_filled)

    msg = f"{header}\n\n"
    msg += f"{grade_emoji} <b>{symbol}</b> — <b>{grade} Setup</b>\n"
    msg += f"Score: [{progress_bar}] {score}/{max_score}\n"
    msg += f"Bias: {bias_emoji} <b>{bias.upper()}</b> | Session: {session}\n\n"

    if conditions:
        msg += "<b>Conditions Met:</b>\n"
        for c in conditions:
            msg += f"  ✓ {c}\n"
        msg += "\n"

    if levels:
        msg += "<b>Trade Levels:</b>\n"
        msg += f"  📍 Entry:  <code>{levels.get('entry', '—')}</code>\n"
        msg += f"  🛑 Stop:   <code>{levels.get('sl', '—')}</code>\n"
        msg += f"  🎯 TP1:    <code>{levels.get('tp1', '—')}</code>  (2R)\n"
        msg += f"  🎯 TP2:    <code>{levels.get('tp2', '—')}</code>  (3R)\n\n"

    msg += "<i>Decision support only — manual execution required.</i>"
    return msg


def send_alert(symbol, analysis, scoring, chart_path=None, alert_stage="setup_developing"):
    msg = format_alert(symbol, analysis, scoring, alert_stage)
    if chart_path:
        return send_photo(chart_path, caption=msg)
    return send_message(msg)


def send_risk_alert(violations, warnings=None):
    msg = "🚨 <b>RISK CONSTITUTION ALERT</b>\n\n"
    for v in violations:
        msg += f"❌ {v}\n"
    if warnings:
        msg += "\n⚠️ <b>Warnings:</b>\n"
        for w in warnings:
            msg += f"  {w}\n"
    msg += "\n<b>Trading suspended per your constitution rules.</b>"
    return send_message(msg)


def send_startup_message(symbols):
    msg = (
        "🚀 <b>Trading Scanner Online</b>\n\n"
        f"Monitoring: <code>{', '.join(symbols)}</code>\n"
        "Timeframes: H4 bias → H1 structure → M15 entry\n\n"
        "Strategy: HTF Bias · BOS · Liquidity Sweeps · FVG · Retest · Rejection\n"
        "Alerts: Standard / A / A+ / 💎 Elite"
    )
    return send_message(msg)
