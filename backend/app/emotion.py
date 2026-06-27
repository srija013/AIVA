import re


EMOTION_KEYWORDS = {
    "sad": [
        "sad", "down", "upset", "crying", "cried", "heartbroken", "depressed",
        "hurt", "unhappy", "miserable", "low", "broken", "lost", "hopeless",
        "empty", "numb", "drained emotionally", "shattered", "devastated"
    ],
    "anxious": [
        "anxious", "anxiety", "worried", "nervous", "tense", "panic", "afraid",
        "scared", "fear", "fearful", "overthinking", "restless", "uneasy",
        "on edge", "paranoid"
    ],
    "stressed": [
        "stressed", "stress", "pressure", "overwhelmed", "burnout", "burned out",
        "too much", "exhausted", "drained", "tired mentally", "can't keep up",
        "so much work", "mentally tired", "loaded", "swamped"
    ],
    "angry": [
        "angry", "mad", "furious", "annoyed", "irritated", "frustrated",
        "hate", "rage", "fed up", "so done", "done with this", "can't stand this",
        "this is ridiculous", "this is so annoying", "pissing me off",
        "getting on my nerves", "leave me alone", "sick of this", "pissed off"
    ],
    "lonely": [
        "lonely", "alone", "isolated", "ignored", "left out", "nobody",
        "no one understands", "by myself", "no one cares", "i have nobody",
        "unseen", "unheard", "invisible"
    ],
    "happy": [
        "happy", "good", "great", "better", "glad", "joy", "joyful",
        "pleased", "content", "thankful", "grateful", "relieved", "peaceful",
        "calm", "proud"
    ],
    "excited": [
        "excited", "thrilled", "looking forward", "can't wait", "motivated",
        "inspired", "energetic", "enthusiastic", "hyped"
    ],
}


EMOTION_SCORES = {
    "sad": -0.8,
    "anxious": -0.7,
    "stressed": -0.7,
    "angry": -0.9,
    "lonely": -0.75,
    "happy": 0.7,
    "excited": 0.85,
    "critical": -1.0,
    "neutral": 0.0,
}


STRONG_PHRASES = {
    "sad": [
        "i feel like giving up",
        "i feel empty",
        "i feel broken",
        "i feel hopeless",
        "nothing feels right",
        "i feel numb",
        "everything hurts",
        "i feel worthless",
        "i can't do this anymore",
    ],
    "stressed": [
        "i am under pressure",
        "too much work",
        "too much to handle",
        "i cannot handle this",
        "i can't handle this",
        "i have too much going on",
        "everything is too much",
        "i'm drowning in work",
    ],
    "anxious": [
        "i feel unsafe",
        "i am scared",
        "i am afraid",
        "what if something goes wrong",
        "i can't stop worrying",
        "my mind won't stop",
        "my chest feels tight",
        "i feel panicky",
    ],
    "lonely": [
        "no one cares",
        "i have nobody",
        "i feel alone",
        "i am all alone",
        "nobody understands me",
        "i feel invisible",
        "no one is there for me",
    ],
    "angry": [
        "i am so done",
        "i'm so done",
        "i can't stand this",
        "this is ridiculous",
        "this is so annoying",
        "i'm fed up",
        "i am fed up",
        "this is getting on my nerves",
        "leave me alone",
        "i hate this",
        "why does this always happen",
        "i'm sick of this",
        "this is bullshit",
    ],
    "happy": [
        "i feel so good",
        "things are going well",
        "i feel at peace",
        "i feel proud of myself",
    ],
    "excited": [
        "i can't wait",
        "this is amazing",
        "i'm really looking forward to this",
    ],
}


CRISIS_PHRASES = [
    "die",
    "i want to die",
    "kill myself",
    "end my life",
    "end it all",
    "don't want to live",
    "do not want to live",
    "wish i was dead",
    "want to disappear",
    "life is pointless",
    "i can't go on",
    "i feel like giving up",
    "nothing matters",
]


LOW_SIGNAL_MESSAGES = {
    "hi", "hello", "hey", "hii", "hiii", "yo",
    "ok", "okay", "kk", "cool", "nice", "thanks", "thank you",
    "good morning", "good afternoon", "good evening",
    "hmm", "hmmm", "yes", "no", "maybe", "alright", "fine"
}


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _count_keyword_hits(normalized: str) -> dict[str, int]:
    hits = {emotion: 0 for emotion in EMOTION_KEYWORDS.keys()}

    for emotion, keywords in EMOTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in normalized:
                hits[emotion] += 1

    for emotion, phrases in STRONG_PHRASES.items():
        for phrase in phrases:
            if phrase in normalized:
                hits[emotion] += 3

    return hits


def _apply_intensity_rules(original_text: str, normalized: str, hits: dict[str, int]) -> None:
    exclamations = original_text.count("!")
    all_caps_words = re.findall(r"\b[A-Z]{3,}\b", original_text)

    if exclamations >= 2 or all_caps_words:
        if hits["angry"] > 0:
            hits["angry"] += 1
        if hits["excited"] > 0:
            hits["excited"] += 1

    if any(p in normalized for p in ["why would they", "why does this", "so unfair", "not fair"]):
        hits["angry"] += 2

    if any(p in normalized for p in ["too much", "so much", "i'm exhausted", "i am exhausted"]):
        hits["stressed"] += 2

    if any(p in normalized for p in ["miss them", "miss her", "miss him", "miss everyone"]):
        hits["lonely"] += 2

    if any(p in normalized for p in ["i feel stuck", "i feel lost", "i don't know anymore"]):
        hits["sad"] += 2
        hits["anxious"] += 1


def _disambiguate(hits: dict[str, int], normalized: str) -> dict[str, int]:
    if hits["angry"] > 0 and hits["stressed"] > 0:
        if any(p in normalized for p in [
            "too much work", "overwhelmed", "under pressure", "can't keep up", "too much to handle"
        ]):
            hits["stressed"] += 2
        if any(p in normalized for p in [
            "ridiculous", "fed up", "annoying", "hate this", "can't stand this", "sick of this"
        ]):
            hits["angry"] += 2

    if hits["sad"] > 0 and hits["lonely"] > 0:
        if any(p in normalized for p in [
            "no one cares", "i have nobody", "alone", "left out", "nobody understands"
        ]):
            hits["lonely"] += 2
        if any(p in normalized for p in [
            "hopeless", "empty", "broken", "crying", "numb", "worthless"
        ]):
            hits["sad"] += 2

    if hits["anxious"] > 0 and hits["stressed"] > 0:
        if any(p in normalized for p in [
            "what if", "worried", "scared", "afraid", "panic", "mind won't stop"
        ]):
            hits["anxious"] += 2
        if any(p in normalized for p in [
            "too much work", "pressure", "burnout", "can't keep up", "swamped"
        ]):
            hits["stressed"] += 2

    if hits["happy"] > 0 and hits["excited"] > 0:
        if any(p in normalized for p in ["can't wait", "thrilled", "looking forward", "hyped"]):
            hits["excited"] += 2
        if any(p in normalized for p in ["peaceful", "grateful", "content", "relieved"]):
            hits["happy"] += 2

    return hits


def _compute_intensity(
    original_text: str,
    normalized: str,
    emotion: str,
    dominant_score: int,
) -> float:
    intensity = 0.0

    intensity += min(dominant_score * 0.22, 0.8)
    intensity += min(original_text.count("!") * 0.05, 0.15)

    if len(normalized.split()) >= 12:
        intensity += 0.12
    if len(normalized.split()) >= 25:
        intensity += 0.12

    if emotion in {"sad", "anxious", "stressed", "angry", "lonely", "critical"}:
        intensity += 0.15

    return round(min(intensity, 1.0), 3)


def _compute_analysis_weight(
    normalized: str,
    emotion: str,
    intensity: float,
    dominant_score: int,
) -> tuple[float, bool]:
    if normalized in LOW_SIGNAL_MESSAGES:
        return 0.1, False

    word_count = len(normalized.split())

    if emotion == "critical":
        return 2.0, True

    if emotion == "neutral":
        if word_count <= 2:
            return 0.1, False
        if word_count <= 5:
            return 0.2, False
        if intensity >= 0.35:
            return 0.5, True
        return 0.25, False

    if dominant_score >= 4 or intensity >= 0.7:
        return 1.5, True

    if dominant_score >= 2 or intensity >= 0.45:
        return 1.0, True

    return 0.5, True

def _infer_emotion_from_sentence(normalized: str) -> tuple[str, int]:
    negative_cues = [
        "i don't know what to do",
        "i dont know what to do",
        "i can't focus",
        "i cant focus",
        "i can't sleep",
        "i cant sleep",
        "i feel weird",
        "i feel off",
        "i feel heavy",
        "i feel bad",
        "i am not okay",
        "i'm not okay",
        "not okay",
        "i need help",
        "i need support",
        "i feel tired",
        "i feel exhausted",
    ]

    if any(p in normalized for p in negative_cues):
        if any(p in normalized for p in ["focus", "work", "deadline", "exam", "assignment"]):
            return "stressed", 2
        if any(p in normalized for p in ["sleep", "worry", "scared", "panic"]):
            return "anxious", 2
        return "sad", 2

    if normalized.startswith(("i feel ", "i am feeling ", "i'm feeling ")):
        if any(p in normalized for p in ["bad", "off", "heavy", "low", "tired"]):
            return "sad", 2

    return "neutral", 0

def detect_emotion_details(text: str) -> dict:
    normalized = _normalize_text(text)

    if not normalized:
        return {
            "emotion": "neutral",
            "sentiment_score": 0.0,
            "emotional_intensity": 0.0,
            "analysis_weight": 0.1,
            "is_meaningful_for_analysis": False,
        }

    if any(p in normalized for p in CRISIS_PHRASES):
        return {
            "emotion": "critical",
            "sentiment_score": -1.0,
            "emotional_intensity": 1.0,
            "analysis_weight": 2.0,
            "is_meaningful_for_analysis": True,
        }

    hits = _count_keyword_hits(normalized)
    _apply_intensity_rules(text, normalized, hits)
    hits = _disambiguate(hits, normalized)

    dominant_emotion = max(hits, key=hits.get)
    dominant_score = hits[dominant_emotion]

    if dominant_score == 0:
        inferred_emotion, inferred_score = _infer_emotion_from_sentence(normalized)

        if inferred_emotion != "neutral":
            intensity = _compute_intensity(
                original_text=text,
                normalized=normalized,
                emotion=inferred_emotion,
                dominant_score=inferred_score,
            )
            weight, meaningful = _compute_analysis_weight(
                normalized=normalized,
                emotion=inferred_emotion,
                intensity=intensity,
                dominant_score=inferred_score,
            )
            return {
                "emotion": inferred_emotion,
                "sentiment_score": EMOTION_SCORES.get(inferred_emotion, 0.0),
                "emotional_intensity": intensity,
                "analysis_weight": weight,
                "is_meaningful_for_analysis": meaningful,
            }

        weight, meaningful = _compute_analysis_weight(
            normalized=normalized,
            emotion="neutral",
            intensity=0.0,
            dominant_score=0,
        )
        return {
            "emotion": "neutral",
            "sentiment_score": 0.0,
            "emotional_intensity": 0.0,
            "analysis_weight": weight,
            "is_meaningful_for_analysis": meaningful,
        }

    if dominant_score == 1 and len(normalized.split()) <= 3:
        weight, meaningful = _compute_analysis_weight(
            normalized=normalized,
            emotion="neutral",
            intensity=0.0,
            dominant_score=0,
        )
        return {
            "emotion": "neutral",
            "sentiment_score": 0.0,
            "emotional_intensity": 0.0,
            "analysis_weight": weight,
            "is_meaningful_for_analysis": meaningful,
        }

    intensity = _compute_intensity(
        original_text=text,
        normalized=normalized,
        emotion=dominant_emotion,
        dominant_score=dominant_score,
    )

    weight, meaningful = _compute_analysis_weight(
        normalized=normalized,
        emotion=dominant_emotion,
        intensity=intensity,
        dominant_score=dominant_score,
    )

    return {
        "emotion": dominant_emotion,
        "sentiment_score": EMOTION_SCORES.get(dominant_emotion, 0.0),
        "emotional_intensity": intensity,
        "analysis_weight": weight,
        "is_meaningful_for_analysis": meaningful,
    }


def detect_emotion(text: str) -> tuple[str, float]:
    details = detect_emotion_details(text)
    return details["emotion"], details["sentiment_score"]