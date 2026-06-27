from collections import defaultdict
from datetime import datetime, timedelta


def get_emotion_streak(emotions):
    if not emotions:
        return None, 0

    last = emotions[-1]
    streak = 1

    for i in range(len(emotions) - 2, -1, -1):
        if emotions[i] == last:
            streak += 1
        else:
            break

    return last, streak


def get_weekly_summary(logs):
    if not logs:
        return {
            "dominant_emotion": "none",
            "total_logs": 0,
            "emotion_counts": {},
            "weighted_emotion_counts": {},
            "meaningful_logs": 0,
            "average_intensity": 0.0,
        }

    cutoff = datetime.utcnow() - timedelta(days=7)
    recent = [l for l in logs if l.created_at >= cutoff]

    if not recent:
        return {
            "dominant_emotion": "none",
            "total_logs": 0,
            "emotion_counts": {},
            "weighted_emotion_counts": {},
            "meaningful_logs": 0,
            "average_intensity": 0.0,
        }

    raw_counts = defaultdict(int)
    weighted_counts = defaultdict(float)

    meaningful_logs = 0
    total_intensity = 0.0

    for log in recent:
        emotion = getattr(log, "detected_emotion", "neutral")
        raw_counts[emotion] += 1

        weight = float(getattr(log, "analysis_weight", 0.1) or 0.1)
        weighted_counts[emotion] += weight

        if getattr(log, "is_meaningful_for_analysis", False):
            meaningful_logs += 1

        total_intensity += float(getattr(log, "emotional_intensity", 0.0) or 0.0)

    dominant = "none"
    if weighted_counts:
        dominant = max(weighted_counts, key=weighted_counts.get)

    avg_intensity = round(total_intensity / len(recent), 3) if recent else 0.0

    return {
        "dominant_emotion": dominant,
        "total_logs": len(recent),
        "emotion_counts": dict(raw_counts),
        "weighted_emotion_counts": {k: round(v, 3) for k, v in weighted_counts.items()},
        "meaningful_logs": meaningful_logs,
        "average_intensity": avg_intensity,
    }