import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import mplfinance as mpf
from datetime import datetime
import config

os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)


def generate_chart(symbol, df, analysis, scoring, timeframe="M15"):
    df_plot = df.tail(60).copy()
    grade = scoring.get("grade", "Standard")
    score = scoring.get("score", 0)
    bias = analysis.get("bias", "neutral")
    levels = analysis.get("levels") or {}
    fvgs = analysis.get("fvgs", [])

    mc = mpf.make_marketcolors(up="#26a69a", down="#ef5350", inherit=True)
    style = mpf.make_mpf_style(
        marketcolors=mc,
        gridstyle="--",
        gridcolor="#2a2a2a",
        facecolor="#131722",
        figcolor="#131722",
        edgecolor="#2a2a2a",
        rc={"axes.labelcolor": "#d1d4dc", "xtick.color": "#787b86", "ytick.color": "#787b86"},
    )

    hlines_data = []
    hlines_colors = []
    hlines_styles = []
    hlines_widths = []

    if levels.get("entry"):
        hlines_data.append(levels["entry"])
        hlines_colors.append("#2196F3")
        hlines_styles.append("--")
        hlines_widths.append(1.5)
    if levels.get("sl"):
        hlines_data.append(levels["sl"])
        hlines_colors.append("#ef5350")
        hlines_styles.append("--")
        hlines_widths.append(1.5)
    if levels.get("tp1"):
        hlines_data.append(levels["tp1"])
        hlines_colors.append("#26a69a")
        hlines_styles.append("--")
        hlines_widths.append(1.5)
    if levels.get("tp2"):
        hlines_data.append(levels["tp2"])
        hlines_colors.append("#00897B")
        hlines_styles.append("-.")
        hlines_widths.append(1.0)

    hlines_kwargs = {}
    if hlines_data:
        hlines_kwargs = {
            "hlines": dict(
                hlines=hlines_data,
                colors=hlines_colors,
                linestyle=hlines_styles,
                linewidths=hlines_widths,
            )
        }

    fig, axes = mpf.plot(
        df_plot,
        type="candle",
        style=style,
        title=f"  {symbol} {timeframe}",
        volume=False,
        returnfig=True,
        figsize=(14, 7),
        **hlines_kwargs,
    )

    ax = axes[0]
    ax.title.set_color("#d1d4dc")

    # Draw FVGs as shaded rectangles
    active_fvgs = [f for f in fvgs if not f["filled"]]
    for fvg in active_fvgs[-4:]:
        color = "#26a69a" if fvg["type"] == "bullish_fvg" else "#ef5350"
        ax.axhspan(fvg["bottom"], fvg["top"], alpha=0.15, color=color)

    # Score / grade box
    grade_colors = {"ELITE": "#b39ddb", "A+": "#ffd54f", "A": "#69f0ae", "Standard": "#4fc3f7"}
    box_color = grade_colors.get(grade, "#4fc3f7")
    from scanner.scoring_engine import GRADE_EMOJI
    emoji = GRADE_EMOJI.get(grade, "")
    score_text = f"{emoji} {grade}  |  Score: {score}/14  |  Bias: {bias.upper()}"
    ax.text(
        0.01, 0.97, score_text,
        transform=ax.transAxes, fontsize=10, color=box_color,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#1e1e2e", edgecolor=box_color, alpha=0.9),
    )

    # Legend
    legend_items = []
    if levels.get("entry"):
        legend_items.append(plt.Line2D([0], [0], color="#2196F3", linestyle="--", label=f"Entry {levels['entry']}"))
    if levels.get("sl"):
        legend_items.append(plt.Line2D([0], [0], color="#ef5350", linestyle="--", label=f"SL {levels['sl']}"))
    if levels.get("tp1"):
        legend_items.append(plt.Line2D([0], [0], color="#26a69a", linestyle="--", label=f"TP1 {levels['tp1']}"))
    if levels.get("tp2"):
        legend_items.append(plt.Line2D([0], [0], color="#00897B", linestyle="-.", label=f"TP2 {levels['tp2']}"))
    if legend_items:
        ax.legend(handles=legend_items, loc="lower left", fontsize=7,
                  facecolor="#1e1e2e", edgecolor="#313244", labelcolor="#d1d4dc")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(config.SCREENSHOTS_DIR, f"{symbol}_{timeframe}_{timestamp}.png")
    plt.savefig(filepath, dpi=100, bbox_inches="tight", facecolor="#131722")
    plt.close(fig)
    return filepath
