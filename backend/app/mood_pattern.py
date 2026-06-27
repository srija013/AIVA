from collections import defaultdict
from typing import List, Dict


NEGATIVE_EMOTIONS = {"sad", "anxious", "stressed", "angry", "lonely"}
POSITIVE_EMOTIONS = {"happy", "excited"}
NEUTRAL_EMOTIONS = {"neutral"}


def count_transitions(emotions: List[str]) -> int:
    if len(emotions) < 2:
        return 0

    transitions = 0
    for i in range(1, len(emotions)):
        if emotions[i] != emotions[i - 1]:
            transitions += 1
    return transitions


def dominant_weighted_emotion(emotions: List[str], weights: List[float]) -> str:
    if not emotions:
        return "neutral"

    totals = defaultdict(float)
    for emotion, weight in zip(emotions, weights):
        totals[emotion] += weight

    if not totals:
        return "neutral"

    return max(totals, key=totals.get)


def classify_mood_pattern(
    emotions: List[str],
    sentiment_scores: List[float],
    analysis_weights: List[float],
    meaningful_flags: List[bool],
) -> Dict[str, str | int | float]:
    filtered = [
        (emotion, score, weight)
        for emotion, score, weight, meaningful in zip(
            emotions, sentiment_scores, analysis_weights, meaningful_flags
        )
        if meaningful
    ]

    if not filtered:
        return {
            "pattern": "neutral_stable",
            "dominant_emotion": "neutral",
            "transition_count": 0,
            "average_sentiment": 0.0,
            "support_message": "No strong recent emotional pattern found.",
        }

    filtered_emotions = [x[0] for x in filtered]
    filtered_scores = [x[1] for x in filtered]
    filtered_weights = [x[2] for x in filtered]

    dom = dominant_weighted_emotion(filtered_emotions, filtered_weights)
    transitions = count_transitions(filtered_emotions)

    total_weight = sum(filtered_weights) or 1.0
    avg_sentiment = round(
        sum(score * weight for score, weight in zip(filtered_scores, filtered_weights)) / total_weight,
        3,
    )

    negative_weight = sum(
        weight for emotion, weight in zip(filtered_emotions, filtered_weights)
        if emotion in NEGATIVE_EMOTIONS
    )
    positive_weight = sum(
        weight for emotion, weight in zip(filtered_emotions, filtered_weights)
        if emotion in POSITIVE_EMOTIONS
    )

    mid = max(1, len(filtered_scores) // 2)
    first_half_scores = filtered_scores[:mid]
    first_half_weights = filtered_weights[:mid]
    second_half_scores = filtered_scores[mid:]
    second_half_weights = filtered_weights[mid:]

    first_avg = (
        sum(s * w for s, w in zip(first_half_scores, first_half_weights)) / (sum(first_half_weights) or 1.0)
    )
    second_avg = (
        sum(s * w for s, w in zip(second_half_scores, second_half_weights)) / (sum(second_half_weights) or 1.0)
        if second_half_scores else first_avg
    )

    improving = second_avg > first_avg + 0.15
    worsening = second_avg < first_avg - 0.15

    if transitions >= 3 and len(set(filtered_emotions)) >= 3:
        pattern = "high_mood_swing"
        support = "Your emotions seem to be shifting a lot recently. Grounding support may help."
    elif negative_weight >= 3.0 and dom in NEGATIVE_EMOTIONS and worsening:
        pattern = "stress_build_up"
        support = "There seems to be building emotional pressure recently."
    elif negative_weight >= 3.0 and dom in NEGATIVE_EMOTIONS:
        pattern = "stable_negative"
        support = "A difficult emotion has been repeating recently."
    elif improving and negative_weight >= 1.0:
        pattern = "recovery_trend"
        support = "Your recent emotional pattern may be improving."
    elif positive_weight >= 3.0 and dom in POSITIVE_EMOTIONS:
        pattern = "stable_positive"
        support = "Your recent emotional pattern looks positive and steady."
    else:
        pattern = "neutral_stable"
        support = "Your recent emotional pattern looks relatively steady."

    return {
        "pattern": pattern,
        "dominant_emotion": dom,
        "transition_count": transitions,
        "average_sentiment": avg_sentiment,
        "support_message": support,
    }