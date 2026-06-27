from typing import List


LOW_SIGNAL_MESSAGES = {
    "hi", "hello", "hey", "yo", "hii", "hiii",
    "good morning", "good afternoon", "good evening",
    "how are you", "sup", "what's up", "ok", "okay",
    "thanks", "thank you", "cool", "nice", "yes", "no", "fine"
}


PATTERN_RECOMMENDATIONS = {
    "stable_negative": [
        "Try one gentle thing instead of trying to fix everything at once.",
        "It may help to slow down and choose one comforting activity for yourself.",
        "You could take a small break and return later with less pressure.",
    ],
    "stress_build_up": [
        "Things seem heavier lately, so taking short breaks may help.",
        "Try reducing pressure by focusing on only one next step.",
        "A small reset might help more than pushing through everything.",
    ],
    "high_mood_swing": [
        "Your mood seems to be shifting a lot, so keeping things gentle may help.",
        "Try to slow the day down a little and avoid piling more pressure on yourself.",
    ],
    "recovery_trend": [
        "You seem to be doing a little better lately. Keep being gentle with yourself.",
        "Something may be helping recently, so it could be worth repeating that routine.",
    ],
    "stable_positive": [
        "You seem steadier lately. Keep doing what has been helping.",
    ],
    "neutral_stable": [],
}


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _split_csv(text: str | None) -> list[str]:
    if not text:
        return []
    return [item.strip().lower() for item in text.split(",") if item.strip()]


def get_support_style(
    emotion: str = "neutral",
    pattern: str = "neutral_stable",
    user=None,
) -> str:
    support_preference = (
        getattr(user, "support_preference", None) or "gentle"
    ).strip().lower()
    preferred_tone = (
        getattr(user, "preferred_response_tone", None) or "calm"
    ).strip().lower()
    personality_type = (
        getattr(user, "personality_type", None) or "balanced"
    ).strip().lower()

    tone_parts = []

    if support_preference == "direct":
        tone_parts.append("Be supportive but more direct and practical than usual.")
    elif support_preference == "balanced":
        tone_parts.append("Be warm, supportive, and balanced between empathy and practical help.")
    else:
        tone_parts.append("Be very gentle, emotionally validating, and reassuring.")

    if preferred_tone == "motivating":
        tone_parts.append("Use an encouraging and uplifting tone.")
    elif preferred_tone == "friendly":
        tone_parts.append("Use a friendly, natural, companion-like tone.")
    elif preferred_tone == "soft":
        tone_parts.append("Use a soft, comforting, low-pressure tone.")
    else:
        tone_parts.append("Use a calm, steady, grounded tone.")

    if personality_type == "introverted":
        tone_parts.append("Keep replies emotionally aware but not overly intense or overly energetic.")
    elif personality_type == "expressive":
        tone_parts.append("You can sound a little more expressive and emotionally warm.")
    else:
        tone_parts.append("Keep replies balanced, natural, and emotionally present.")

    if emotion in {"sad", "lonely"}:
        tone_parts.append("Prioritize comfort, validation, and gentle companionship.")
    elif emotion in {"stressed", "anxious"}:
        tone_parts.append("Reduce pressure and help the user slow things down.")
    elif emotion in {"happy", "excited"}:
        tone_parts.append("Match the positive mood without sounding overhyped.")
    elif emotion == "angry":
        tone_parts.append("Stay calm, validating, and non-escalatory.")

    if pattern in {"stable_negative", "stress_build_up"}:
        tone_parts.append("The user may be emotionally strained lately, so avoid sounding demanding or overly analytical.")
    elif pattern == "recovery_trend":
        tone_parts.append("Acknowledge signs of improvement gently without overclaiming.")

    return " ".join(tone_parts)

def should_show_recommendations(
    message: str,
    current_emotion: str,
    emotional_intensity: float,
    sentiment_score: float,
    pattern: str,
    is_meaningful_for_analysis: bool,
) -> bool:
    text = _normalize(message)

    if text in LOW_SIGNAL_MESSAGES:
        return False

    if not is_meaningful_for_analysis:
        return False

    if current_emotion in {"neutral", "happy", "excited", "critical"}:
        return False

    # Only show recommendations for clearly heavy emotional messages
    if current_emotion in {"sad", "lonely", "stressed", "anxious", "angry"}:
        return emotional_intensity >= 0.72 or sentiment_score <= -0.75

    # Pattern-based recs only for serious repeated negative patterns
    if pattern in {"stable_negative", "stress_build_up"}:
        return emotional_intensity >= 0.65

    return False


def get_relief_tools(user, emotion: str, pattern: str) -> List[str]:
    disliked = set(_split_csv(getattr(user, "disliked_support_styles", None)))
    preferences = set(_split_csv(getattr(user, "coping_preferences", None)))

    tools: list[str] = []

    def add_tool(name: str, enabled: bool = True):
        if enabled and name not in disliked and name not in tools:
            tools.append(name)

    if emotion in {"anxious", "stressed"}:
        add_tool("breathing", getattr(user, "likes_breathing", True))
        add_tool("music", getattr(user, "likes_music", False))
        add_tool("drawing", getattr(user, "likes_drawing", False))
    elif emotion in {"sad", "lonely"}:
        add_tool("music", getattr(user, "likes_music", False))
        add_tool("drawing", getattr(user, "likes_drawing", False))
        add_tool("journaling", getattr(user, "likes_journaling", False))
    else:
        add_tool("music", getattr(user, "likes_music", False))
        add_tool("drawing", getattr(user, "likes_drawing", False))

    for pref in preferences:
        if pref in {"breathing", "drawing", "journaling", "music", "games", "grounding"}:
            add_tool(pref, True)

    return tools[:4]


def get_personalized_preference_recommendations(user, emotion: str) -> list[str]:
    items: list[str] = []

    favorite_movie = (getattr(user, "favorite_movie", None) or "").strip()
    favorite_song = (getattr(user, "favorite_song", None) or "").strip()
    favorite_activity = (getattr(user, "favorite_activity", None) or "").strip()
    comfort_activity = (getattr(user, "comfort_activity", None) or "").strip()

    if emotion in {"lonely", "sad"}:
        if favorite_movie:
            items.append(
                f"You could watch your favorite movie {favorite_movie}; it might feel comforting right now."
            )
        if favorite_song:
            items.append(
                f"Maybe listening to your favorite song {favorite_song} could help a little."
            )
        if comfort_activity:
            items.append(
                f"You could try {comfort_activity} if that usually helps you feel better."
            )
    elif emotion in {"stressed", "anxious"}:
        if comfort_activity:
            items.append(
                f"Since things feel heavy, maybe try {comfort_activity} for a short reset."
            )
        if favorite_song:
            items.append(
                f"You could play {favorite_song} and give yourself a calmer moment."
            )
    else:
        if favorite_activity:
            items.append(
                f"You could spend a little time on {favorite_activity} if that feels nice today."
            )

    return items


def get_recommendations(user, pattern: str, relief_tools: list[str], emotion: str, limit: int = 3) -> list[str]:
    items = []

    personalized = get_personalized_preference_recommendations(user, emotion)
    items.extend(personalized)
    items.extend(PATTERN_RECOMMENDATIONS.get(pattern, []))

    tool_map = {
        "breathing": "A short breathing reset may help you settle a little.",
        "drawing": "You could try a few minutes of doodling to let some stress out gently.",
        "journaling": "Writing a little may help you get some of this out of your head.",
        "music": "Playing music you enjoy might help soften the moment.",
        "games": "A soft reset activity might help if you want gentle distraction.",
        "grounding": "A small grounding exercise may help you feel a little more settled.",
    }

    for tool in relief_tools:
        suggestion = tool_map.get(tool)
        if suggestion and suggestion not in items:
            items.append(suggestion)

    deduped = []
    seen = set()
    for item in items:
        key = item.strip().lower()
        if key not in seen:
            deduped.append(item)
            seen.add(key)

    return deduped[:limit]