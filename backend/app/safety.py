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


def detect_crisis(message: str) -> bool:
    text = message.lower().strip()
    return any(phrase in text for phrase in CRISIS_PHRASES)


def get_crisis_response() -> str:
    return (
        "I'm really sorry you're feeling this way. You don’t have to go through this alone. "
        "If you can, please consider reaching out to someone you trust or a professional. "
        "I'm here with you — do you want to talk about what’s making things feel this hard?"
    )