from sqlalchemy.orm import Session
from app.models import Conversation


def get_recent_conversations(db: Session, user_id: str, limit: int = 5):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
        .all()
    )

    conversations = list(reversed(conversations))

    recent_context = []
    for convo in conversations:
        recent_context.append(f"User: {convo.user_text}")
        recent_context.append(f"Assistant: {convo.ai_text}")

    return recent_context


def get_relevant_past_conversations(db: Session, user_id: str, message: str, limit: int = 3):
    words = [word.strip(".,!?").lower() for word in message.split() if len(word) > 3]

    all_conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
        .all()
    )

    scored = []
    for convo in all_conversations:
        score = 0
        user_text_lower = convo.user_text.lower()
        ai_text_lower = convo.ai_text.lower()

        for word in words:
            if word in user_text_lower or word in ai_text_lower:
                score += 1

        if score > 0:
            summary = f"User: {convo.user_text} | Assistant: {convo.ai_text}"
            scored.append((score, summary))

    scored.sort(key=lambda x: x[0], reverse=True)

    seen = set()
    results = []
    for _, item in scored:
        if item not in seen:
            results.append(item)
            seen.add(item)
        if len(results) >= limit:
            break

    return results