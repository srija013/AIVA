import re
from typing import List
from sqlalchemy.orm import Session
from app.models import Memory


LOW_SIGNAL_MESSAGES = {
    "hi", "hello", "hey", "yo", "hii", "hiii",
    "good morning", "good afternoon", "good evening",
    "how are you", "sup", "what's up", "ok", "okay",
    "thanks", "thank you", "cool", "nice", "yes", "no", "fine"
}

TOOL_ACTIVITY_PATTERNS = [
    r"\bbreathing helped me\b",
    r"\bjournaling helped me\b",
    r"\bdrawing helped me\b",
    r"\bmusic helped me\b",
    r"\bgames helped me\b",
    r"\bgrounding helped me\b",
    r"\bopened .* screen\b",
    r"\bused .* tool\b",
    r"\bplayed .* game\b",
]

IDENTITY_PATTERNS = [
    r"\bmy name is\b",
    r"\bi am called\b",
    r"\bi'm called\b",
    r"\bi live in\b",
    r"\bi study at\b",
    r"\bi work at\b",
    r"\bi am a\b",
    r"\bi'm a\b",
]

PREFERENCE_PATTERNS = [
    r"\bmy favorite\b",
    r"\bi like\b",
    r"\bi love\b",
    r"\bi prefer\b",
    r"\bi enjoy\b",
    r"\bhelps me calm down\b",
    r"\bcomforts me\b",
    r"\bmakes me feel better\b",
]

IMPORTANT_EVENT_PATTERNS = [
    r"\bexam\b",
    r"\binterview\b",
    r"\bdeadline\b",
    r"\bpresentation\b",
    r"\bmeeting\b",
    r"\btrip\b",
    r"\bflight\b",
    r"\bappointment\b",
]

EMOTIONAL_PATTERN_PATTERNS = [
    r"\bi feel\b",
    r"\bi've been feeling\b",
    r"\bi have been feeling\b",
    r"\bi often feel\b",
    r"\bi usually feel\b",
    r"\bi get stressed\b",
    r"\bi get anxious\b",
    r"\bi feel lonely\b",
    r"\bi feel sad\b",
    r"\bi struggle with\b",
    r"\bi am struggling with\b",
    r"\bi'm struggling with\b",
]


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _infer_memory_type(text: str) -> str:
    if _matches_any(text, IDENTITY_PATTERNS):
        return "profile"
    if _matches_any(text, PREFERENCE_PATTERNS):
        return "preference"
    if _matches_any(text, IMPORTANT_EVENT_PATTERNS):
        return "important_event"
    if _matches_any(text, EMOTIONAL_PATTERN_PATTERNS):
        return "emotional_pattern"
    return "general"


def _infer_importance_score(text: str, emotion: str) -> float:
    score = 0.75

    if _matches_any(text, IDENTITY_PATTERNS):
        score = max(score, 0.90)
    if _matches_any(text, PREFERENCE_PATTERNS):
        score = max(score, 0.85)
    if _matches_any(text, IMPORTANT_EVENT_PATTERNS):
        score = max(score, 0.92)
    if _matches_any(text, EMOTIONAL_PATTERN_PATTERNS):
        score = max(score, 0.88)

    if emotion in {"sad", "anxious", "stressed", "lonely", "angry", "critical"}:
        score = max(score, 0.90)

    return min(score, 0.98)


def should_store_as_memory(message: str, emotion: str) -> bool:
    text = _normalize(message)

    if not text:
        return False

    if text in LOW_SIGNAL_MESSAGES:
        return False

    if len(text) < 12:
        return False

    if _matches_any(text, TOOL_ACTIVITY_PATTERNS):
        return False

    if text.startswith("http://") or text.startswith("https://"):
        return False

    if _matches_any(text, IDENTITY_PATTERNS):
        return True

    if _matches_any(text, PREFERENCE_PATTERNS):
        return True

    if _matches_any(text, IMPORTANT_EVENT_PATTERNS):
        return True

    if _matches_any(text, EMOTIONAL_PATTERN_PATTERNS):
        return True

    if emotion in {"sad", "anxious", "stressed", "lonely", "angry", "critical"} and len(text) >= 20:
        return True

    return False


def save_memory(db: Session, user_id: str, message: str, emotion: str) -> None:
    text = " ".join(message.strip().split())
    normalized = _normalize(text)

    if not should_store_as_memory(text, emotion):
        return

    memory_type = _infer_memory_type(normalized)
    importance_score = _infer_importance_score(normalized, emotion)

    existing_memories = (
        db.query(Memory)
        .filter(Memory.user_id == user_id)
        .order_by(Memory.created_at.desc())
        .limit(30)
        .all()
    )

    for memory in existing_memories:
        existing_text = _normalize(memory.memory_text)
        if existing_text == normalized:
            return

        if memory.memory_type == memory_type:
            if normalized in existing_text or existing_text in normalized:
                return

    new_memory = Memory(
        user_id=user_id,
        memory_text=text,
        memory_type=memory_type,
        importance_score=importance_score,
        emotion_tag=emotion if emotion else "neutral",
    )

    db.add(new_memory)
    db.commit()


def retrieve_relevant_memories(
    db: Session,
    user_id: str,
    message: str,
    limit: int = 3,
) -> List[str]:
    query_text = _normalize(message)

    memories = (
        db.query(Memory)
        .filter(Memory.user_id == user_id)
        .order_by(Memory.importance_score.desc(), Memory.created_at.desc())
        .limit(50)
        .all()
    )

    if not memories:
        return []

    query_words = set(query_text.split())
    scored = []

    for memory in memories:
        mem_text = _normalize(memory.memory_text)
        mem_words = set(mem_text.split())

        overlap = len(query_words.intersection(mem_words))
        recency_bonus = 0.05
        importance = float(memory.importance_score or 0.0)

        score = overlap * 1.2 + importance + recency_bonus

        if _matches_any(query_text, IMPORTANT_EVENT_PATTERNS) and memory.memory_type == "important_event":
            score += 0.5
        if _matches_any(query_text, PREFERENCE_PATTERNS) and memory.memory_type == "preference":
            score += 0.5
        if _matches_any(query_text, EMOTIONAL_PATTERN_PATTERNS) and memory.memory_type == "emotional_pattern":
            score += 0.5

        if overlap > 0 or importance >= 0.9:
            scored.append((score, memory.memory_text))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    seen = set()
    for _, text in scored:
        key = _normalize(text)
        if key not in seen:
            results.append(text)
            seen.add(key)
        if len(results) >= limit:
            break

    return results