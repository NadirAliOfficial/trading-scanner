import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date

from database.db_manager import (
    init_db, get_all_trades, get_active_setups,
    get_daily_stats, get_weekly_stats, get_risk_log,
    get_journal_entries, save_journal_entry, log_trade, close_trade,
)
import config

st.set_page_config(
    page_title="Trading OS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 1.6rem; }
.grade-elite { color: #b39ddb; font-weight: 700; }
.grade-aplus { color: #ffd54f; font-weight: 700; }
.grade-a     { color: #69f0ae; font-weight: 700; }
.grade-std   { color: #4fc3f7; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

GRADE_EMOJI = {"ELITE": "💎", "A+": "🥇", "A": "🥈", "Standard": "🥉"}
BIAS_ICON = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}


def main():
    init_db()

    with st.sidebar:
        st.title("📊 Trading OS")
        st.caption(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.divider()
        page = st.radio(
            "Navigation",
            ["Dashboard", "Active Setups", "Trade Journal", "Analytics", "Daily Review", "Risk Status"],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption(f"Scanning: {', '.join(config.SYMBOLS)}")
        st.caption(f"HTF: {config.HTF} | MTF: {config.MTF} | LTF: {config.LTF}")

    if page == "Dashboard":
        show_dashboard()
    elif page == "Active Setups":
        show_active_setups()
    elif page == "Trade Journal":
        show_journal()
    elif page == "Analytics":
        show_analytics()
    elif page == "Daily Review":
        show_daily_review()
    elif page == "Risk Status":
        show_risk_status()


def show_dashboard():
    st.header("Dashboard")
    daily = get_daily_stats()
    weekly = get_weekly_stats()

    c1, c2, c3, c4, c5 = st.columns(5)
    d_total = daily["total"] or 0
    d_wins = daily["wins"] or 0
    d_wr = f"{d_wins / d_total * 100:.0f}%" if d_total else "—"
    w_total = weekly["total"] or 0
    w_wins = weekly["wins"] or 0
    w_wr = f"{w_wins / w_total * 100:.0f}%" if w_total else "—"

    c1.metric("Today Trades", d_total)
    c2.metric("Today Win Rate", d_wr)
    c3.metric("Today Avg RR", f"{daily['avg_rr']:.2f}" if daily["avg_rr"] else "—")
    c4.metric("Week Trades", w_total)
    c5.metric("Week Win Rate", w_wr)

    st.divider()
    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.subheader("Recent Setups")
        setups = get_active_setups(8)
        if setups:
            for s in setups:
                g = s.get("grade", "Standard")
                em = GRADE_EMOJI.get(g, "📊")
                bi = BIAS_ICON.get(s.get("bias", "neutral"), "⚪")
                detected = s.get("detected_at", "")[:16]
                st.write(
                    f"{em} **{s['symbol']}** | {g} (Score {s['score']}) | "
                    f"{bi} {s.get('bias', '')} | {s.get('session', '')} | {detected}"
                )
        else:
            st.info("No setups detected yet. Start the scanner to populate this.")

    with col_right:
        st.subheader("Constitution")
        st.write(f"Max risk/trade: **{config.MAX_RISK_PER_TRADE}%**")
        st.write(f"Daily DD limit: **{config.MAX_DAILY_DRAWDOWN}%**")
        st.write(f"Weekly DD limit: **{config.MAX_WEEKLY_DRAWDOWN}%**")
        st.write(f"Max consec. losses: **{config.MAX_CONSECUTIVE_LOSSES}**")
        st.write(f"Min alert score: **{config.SCORE_STANDARD}**")

    risk_log = get_risk_log(50)
    if risk_log:
        st.divider()
        st.subheader("Equity / Drawdown Trend")
        df_risk = pd.DataFrame(risk_log).sort_values("logged_at")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_risk["logged_at"], y=df_risk["equity"], name="Equity", line=dict(color="#26a69a")))
        fig.add_trace(go.Scatter(x=df_risk["logged_at"], y=df_risk["daily_dd"], name="Daily DD %", yaxis="y2", line=dict(color="#ef5350", dash="dash")))
        fig.update_layout(
            yaxis2=dict(overlaying="y", side="right", title="DD %"),
            height=300, margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation="h"),
        )
        st.plotly_chart(fig, use_container_width=True)


def show_active_setups():
    st.header("Active Setups")
    setups = get_active_setups(50)
    if not setups:
        st.info("No setups in database yet.")
        return

    df = pd.DataFrame(setups)
    grades = df["grade"].dropna().unique().tolist()
    selected = st.multiselect("Grade filter", ["ELITE", "A+", "A", "Standard"], default=grades)
    df = df[df["grade"].isin(selected)]

    if df.empty:
        st.info("No setups match the filter.")
        return

    display_cols = ["detected_at", "symbol", "timeframe", "bias", "grade", "score", "entry", "sl", "tp1", "session"]
    display_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[display_cols].reset_index(drop=True), use_container_width=True)

    if st.checkbox("Show chart screenshots"):
        for s in setups[:5]:
            cp = s.get("chart_path")
            if cp and os.path.exists(cp):
                st.image(cp, caption=f"{s['symbol']} — {s['grade']} (Score {s['score']})", use_column_width=True)


def show_journal():
    st.header("Trade Journal")
    tab1, tab2 = st.tabs(["Log Trade", "View Trades"])

    with tab1:
        with st.form("log_trade_form"):
            c1, c2 = st.columns(2)
            symbol = c1.selectbox("Symbol", config.SYMBOLS)
            direction = c2.radio("Direction", ["Buy", "Sell"], horizontal=True)
            c3, c4, c5 = st.columns(3)
            entry = c3.number_input("Entry", format="%.5f", value=0.0)
            sl = c4.number_input("Stop Loss", format="%.5f", value=0.0)
            tp = c5.number_input("Take Profit", format="%.5f", value=0.0)
            grade = st.selectbox("Setup Grade", ["Standard", "A", "A+", "ELITE"])
            notes = st.text_area("Notes", height=80)
            if st.form_submit_button("Log Trade", type="primary"):
                tid = log_trade(symbol, direction, entry, sl, tp, grade=grade, notes=notes)
                st.success(f"Trade #{tid} logged.")

    with tab2:
        trades = get_all_trades()
        if trades:
            df = pd.DataFrame(trades)
            st.dataframe(df, use_container_width=True)

            st.divider()
            st.subheader("Close a Trade")
            with st.form("close_trade_form"):
                trade_ids = [t["id"] for t in trades if t.get("outcome") is None]
                if trade_ids:
                    tid = st.selectbox("Trade ID", trade_ids)
                    exit_p = st.number_input("Exit Price", format="%.5f")
                    outcome = st.radio("Outcome", ["win", "loss", "breakeven"], horizontal=True)
                    rr = st.number_input("RR Achieved", value=0.0, step=0.1)
                    close_notes = st.text_input("Notes")
                    if st.form_submit_button("Close Trade"):
                        close_trade(tid, exit_p, outcome, rr, close_notes)
                        st.success(f"Trade #{tid} closed as {outcome}.")
                        st.rerun()
                else:
                    st.info("No open trades to close.")
        else:
            st.info("No trades logged yet.")


def show_analytics():
    st.header("Performance Analytics")
    trades = get_all_trades()
    if not trades:
        st.info("No trade data yet. Log some trades first.")
        return

    df = pd.DataFrame(trades)
    df["opened_at"] = pd.to_datetime(df["opened_at"])

    c1, c2 = st.columns(2)

    with c1:
        if "outcome" in df.columns and df["outcome"].notna().any():
            oc = df["outcome"].value_counts()
            fig = px.pie(values=oc.values, names=oc.index, title="Win / Loss / Breakeven",
                         color_discrete_map={"win": "#26a69a", "loss": "#ef5350", "breakeven": "#ffd54f"})
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if "grade" in df.columns and "outcome" in df.columns:
            g_df = df[df["outcome"].notna()].groupby(["grade", "outcome"]).size().reset_index(name="count")
            fig = px.bar(g_df, x="grade", y="count", color="outcome", title="Outcomes by Setup Grade",
                         color_discrete_map={"win": "#26a69a", "loss": "#ef5350", "breakeven": "#ffd54f"})
            st.plotly_chart(fig, use_container_width=True)

    if "rr_achieved" in df.columns and df["rr_achieved"].notna().any():
        fig = px.histogram(df[df["rr_achieved"].notna()], x="rr_achieved",
                           title="RR Distribution", nbins=20, color_discrete_sequence=["#2196F3"])
        st.plotly_chart(fig, use_container_width=True)

    if "symbol" in df.columns and "outcome" in df.columns:
        sym_df = df[df["outcome"].notna()].groupby(["symbol", "outcome"]).size().reset_index(name="count")
        fig = px.bar(sym_df, x="symbol", y="count", color="outcome", title="Performance by Symbol",
                     color_discrete_map={"win": "#26a69a", "loss": "#ef5350", "breakeven": "#ffd54f"})
        st.plotly_chart(fig, use_container_width=True)

    if "session" in df.columns and "outcome" in df.columns:
        ses_df = df[df["outcome"].notna()].groupby(["session", "outcome"]).size().reset_index(name="count")
        fig = px.bar(ses_df, x="session", y="count", color="outcome", title="Performance by Session",
                     color_discrete_map={"win": "#26a69a", "loss": "#ef5350", "breakeven": "#ffd54f"})
        st.plotly_chart(fig, use_container_width=True)


def show_daily_review():
    st.header("Daily Trading Review")
    st.caption("End-of-day reflection — stored and used for coaching analysis.")

    trades = get_all_trades()
    open_trades = [t for t in trades if t.get("outcome") is not None]

    with st.form("daily_review_form"):
        trade_id = None
        if open_trades:
            trade_options = {f"#{t['id']} — {t['symbol']} {t['direction']} ({t['outcome']})": t["id"] for t in open_trades[:20]}
            selected_label = st.selectbox("Link to trade (optional)", ["None"] + list(trade_options.keys()))
            trade_id = trade_options.get(selected_label)

        followed_plan = st.radio(
            "Did you follow your trading plan?",
            ["Yes — fully", "Yes — mostly", "No — deviated", "No trades today"],
            horizontal=True,
        )
        outcome = st.radio(
            "Overall outcome today?",
            ["Profitable", "Breakeven", "Loss", "No trades"],
            horizontal=True,
        )
        moved_stop = st.radio(
            "Did you move your stop loss?",
            ["No — held discipline", "Yes — to breakeven", "Yes — widened (bad)", "N/A"],
            horizontal=True,
        )
        better_entry = st.radio(
            "Was there a better entry available?",
            ["No — entry was optimal", "Yes — could have waited", "Yes — entered too early", "N/A"],
            horizontal=True,
        )
        emotions = st.multiselect(
            "Emotions experienced during session:",
            ["Calm & focused", "FOMO", "Revenge trading urge", "Overconfident",
             "Anxious", "Hesitant", "Impatient", "Disciplined", "Frustrated"],
        )
        notes = st.text_area("Lessons learned / notes:", height=120)

        if st.form_submit_button("Submit Review", type="primary"):
            save_journal_entry(trade_id, followed_plan, outcome, moved_stop, better_entry, emotions, notes)
            st.success("Review saved. Great job staying accountable.")
            st.balloons()

    st.divider()
    st.subheader("Past Reviews")
    entries = get_journal_entries()
    if entries:
        st.dataframe(pd.DataFrame(entries), use_container_width=True)
    else:
        st.info("No reviews yet.")


def show_risk_status():
    st.header("Risk Management Status")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Max Risk / Trade", f"{config.MAX_RISK_PER_TRADE}%")
    c2.metric("Daily DD Limit", f"{config.MAX_DAILY_DRAWDOWN}%")
    c3.metric("Weekly DD Limit", f"{config.MAX_WEEKLY_DRAWDOWN}%")
    c4.metric("Max Consec. Losses", config.MAX_CONSECUTIVE_LOSSES)

    st.divider()
    risk_log = get_risk_log(200)
    if risk_log:
        df = pd.DataFrame(risk_log).sort_values("logged_at")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["logged_at"], y=df["daily_dd"], name="Daily DD %", line=dict(color="#ef5350")))
        fig.add_trace(go.Scatter(x=df["logged_at"], y=df["weekly_dd"], name="Weekly DD %", line=dict(color="#ffd54f")))
        fig.add_hline(y=config.MAX_DAILY_DRAWDOWN, line_dash="dash", line_color="#ef5350", annotation_text="Daily Limit")
        fig.add_hline(y=config.MAX_WEEKLY_DRAWDOWN, line_dash="dash", line_color="#ffd54f", annotation_text="Weekly Limit")
        fig.update_layout(title="Drawdown History", height=350)
        st.plotly_chart(fig, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df["logged_at"], y=df["consecutive_losses"], name="Consec. Losses",
                                  fill="tozeroy", line=dict(color="#b39ddb")))
        fig2.add_hline(y=config.MAX_CONSECUTIVE_LOSSES, line_dash="dash", line_color="#ef5350", annotation_text="Limit")
        fig2.update_layout(title="Consecutive Loss Tracker", height=250)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No risk log data yet. Start the scanner to begin tracking.")

    st.divider()
    st.subheader("Constitution Rules")
    rules = [
        f"Maximum risk per trade: {config.MAX_RISK_PER_TRADE}% of account balance",
        f"Maximum daily drawdown: {config.MAX_DAILY_DRAWDOWN}% — scanner suspends alerts if breached",
        f"Maximum weekly drawdown: {config.MAX_WEEKLY_DRAWDOWN}% — scanner suspends alerts if breached",
        f"Maximum {config.MAX_CONSECUTIVE_LOSSES} consecutive losses before trading is paused",
        "Elite trades: only allowed when score ≥ 12 and daily DD < 50% of limit",
        "Position sizing: automatic based on risk % and SL distance",
    ]
    for r in rules:
        st.write(f"• {r}")


if __name__ == "__main__":
    main()
