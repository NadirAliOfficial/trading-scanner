import config

GRADE_EMOJI = {
    "ELITE": "💎",
    "A+": "🥇",
    "A": "🥈",
    "Standard": "🥉",
}

GRADE_COLOR = {
    "ELITE": "purple",
    "A+": "gold",
    "A": "green",
    "Standard": "blue",
}


def classify_setup(score):
    if score >= config.SCORE_ELITE:
        return "ELITE"
    if score >= config.SCORE_A_PLUS:
        return "A+"
    if score >= config.SCORE_A:
        return "A"
    if score >= config.SCORE_STANDARD:
        return "Standard"
    return None


def score_setup(analysis):
    score = 0
    breakdown = []

    bias = analysis.get("bias", "neutral")
    if bias != "neutral":
        score += 2
        breakdown.append(f"HTF Bias ({bias}): +2")

    if analysis.get("bos"):
        score += 2
        breakdown.append("BOS confirmed: +2")

    if analysis.get("liquidity_sweep"):
        score += 2
        breakdown.append("Liquidity Sweep: +2")

    active_fvgs = [f for f in analysis.get("fvgs", []) if not f["filled"]]
    if active_fvgs:
        score += 2
        breakdown.append(f"Active FVG ({len(active_fvgs)}): +2")

    if analysis.get("retest"):
        score += 2
        breakdown.append(f"Retest ({analysis['retest']['type']}): +2")

    if analysis.get("rejection"):
        score += 2
        breakdown.append(f"Rejection candle ({analysis['rejection']['type']}): +2")

    session = analysis.get("session", "")
    if session in ("london", "new_york", "london_ny_overlap"):
        score += 1
        breakdown.append(f"Active session ({session}): +1")

    levels = analysis.get("levels") or {}
    if levels.get("rr", 0) >= 2:
        score += 1
        breakdown.append("RR >= 2: +1")

    grade = classify_setup(score)

    return {
        "score": score,
        "max_score": 14,
        "grade": grade,
        "breakdown": breakdown,
    }
