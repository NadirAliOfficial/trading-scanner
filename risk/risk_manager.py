from datetime import date
import config
from database.db_manager import get_recent_losses


class RiskManager:
    def __init__(self):
        self._daily_start = None
        self._weekly_start = None
        self._today = date.today()

    def _reset_if_new_day(self, balance):
        today = date.today()
        if self._today != today:
            self._daily_start = balance
            self._today = today

    def seed_balance(self, balance):
        if self._daily_start is None:
            self._daily_start = balance
        if self._weekly_start is None:
            self._weekly_start = balance

    def check_risk(self, balance, equity):
        self.seed_balance(balance)
        self._reset_if_new_day(balance)

        violations = []
        warnings = []

        daily_dd = (self._daily_start - equity) / self._daily_start * 100
        weekly_dd = (self._weekly_start - equity) / self._weekly_start * 100

        if daily_dd >= config.MAX_DAILY_DRAWDOWN:
            violations.append(
                f"Daily drawdown {daily_dd:.2f}% exceeds limit ({config.MAX_DAILY_DRAWDOWN}%)"
            )
        elif daily_dd >= config.MAX_DAILY_DRAWDOWN * 0.75:
            warnings.append(f"Daily drawdown at {daily_dd:.2f}% — approaching limit")

        if weekly_dd >= config.MAX_WEEKLY_DRAWDOWN:
            violations.append(
                f"Weekly drawdown {weekly_dd:.2f}% exceeds limit ({config.MAX_WEEKLY_DRAWDOWN}%)"
            )

        consec_losses = len(get_recent_losses(config.MAX_CONSECUTIVE_LOSSES))
        if consec_losses >= config.MAX_CONSECUTIVE_LOSSES:
            violations.append(
                f"{consec_losses} consecutive losses — trading suspended per constitution"
            )

        return {
            "allowed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "daily_drawdown": round(daily_dd, 2),
            "weekly_drawdown": round(weekly_dd, 2),
            "consecutive_losses": consec_losses,
            "daily_start": self._daily_start,
            "weekly_start": self._weekly_start,
        }

    def calculate_position_size(self, account_balance, entry, sl, pip_value=10.0, digits=5):
        """Return lot size based on MAX_RISK_PER_TRADE%."""
        risk_amount = account_balance * (config.MAX_RISK_PER_TRADE / 100)
        point = 0.00001 if digits == 5 else 0.001
        sl_pips = abs(entry - sl) / (point * 10)
        if sl_pips < 1:
            return 0.01
        lot_size = risk_amount / (sl_pips * pip_value)
        return round(max(0.01, min(lot_size, 100.0)), 2)

    def is_elite_trade_allowed(self, scoring, risk_status):
        """Elite trades require ELITE grade + no violations."""
        return (
            scoring.get("grade") == "ELITE"
            and risk_status.get("allowed")
            and risk_status.get("daily_drawdown", 99) < config.MAX_DAILY_DRAWDOWN * 0.5
        )
