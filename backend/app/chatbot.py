from anthropic import Anthropic
from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from app.recommendation import get_support_style


def build_system_prompt() -> str:
    return """
You are a voice-based AI companion inside a mobile app.

Your personality:
- warm
- natural
- emotionally aware
- supportive
- human-friendly
- never robotic

Rules:
- keep responses concise and easy to speak aloud
- sound like a caring human companion
- acknowledge the user's emotional state naturally
- use context from recent chats, relevant older chats, important memories, and user support preferences
- use memory only when relevant
- do not mention 'memory retrieval', 'sentiment score', or technical terms
- do not dump too many old details at once
- do not overload the user with too much advice in one reply
- recommendations may be shown separately in the app, so keep the spoken reply emotionally supportive first
- if the user sounds stressed or anxious, be calming and practical
- if the user sounds sad, be gentle and comforting
- if the user sounds happy, be warm and encouraging
- if the user sounds angry, be calm and de-escalating
- if the user sounds lonely, be especially warm and connecting
- match your tone to the user's preference if provided
""".strip()


def _csv_to_list(text: str | None) -> list[str]:
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def _build_user_preference_summary(user) -> str:
    if not user:
        return "No user preferences available."

    coping_preferences = _csv_to_list(getattr(user, "coping_preferences", None))
    disliked_support_styles = _csv_to_list(getattr(user, "disliked_support_styles", None))

    lines = [
        f"Preferred response tone: {getattr(user, 'preferred_response_tone', None) or 'not specified'}",
        f"Support preference: {getattr(user, 'support_preference', None) or 'not specified'}",
        f"Personality type: {getattr(user, 'personality_type', None) or 'not specified'}",
    ]

    if coping_preferences:
        lines.append("Preferred coping styles: " + ", ".join(coping_preferences))
    else:
        lines.append("Preferred coping styles: not specified")

    if disliked_support_styles:
        lines.append("Disliked support styles: " + ", ".join(disliked_support_styles))
    else:
        lines.append("Disliked support styles: none known")

    return "\n".join(lines)


def generate_reply(
    user_message: str,
    emotion: str,
    memories: list[str],
    recent_context: list[str],
    relevant_past: list[str],
    mood_pattern: str = "neutral_stable",
    user=None,
) -> str:
    support_style = get_support_style(emotion, mood_pattern, user=user)

    if not ANTHROPIC_API_KEY:
        extra_context = ""
        if memories:
            extra_context += " I remember you mentioned " + "; ".join(memories[:2]) + "."
        if relevant_past:
            extra_context += " I’m keeping our earlier conversation in mind."

        tone = getattr(user, "preferred_response_tone", None) if user else None
        support_pref = getattr(user, "support_preference", None) if user else None

        prefix = "I’m here with you."
        if tone == "motivating":
            prefix = "I’m with you, and we can handle this one step at a time."
        elif tone == "soft":
            prefix = "I’m here with you gently."
        elif tone == "friendly":
            prefix = "I’m here with you."
        elif tone == "calm":
            prefix = "Let’s slow this down together."

        if emotion == "sad":
            return (
                f"That sounds really heavy.{extra_context} "
                f"{prefix} Want to tell me a little more about what’s hurting most right now?"
            )
        if emotion == "anxious":
            return (
                f"It makes sense that this feels overwhelming.{extra_context} "
                f"{prefix} What feels like the hardest part right now?"
            )
        if emotion == "stressed":
            return (
                f"You’ve got a lot on your mind.{extra_context} "
                f"{prefix} What feels most urgent right now?"
            )
        if emotion == "happy":
            return (
                f"That’s really nice to hear!{extra_context} "
                f"I’m glad this feels good. What’s been the best part of it?"
            )
        if emotion == "angry":
            return (
                f"I can understand why that would feel frustrating.{extra_context} "
                f"{prefix} Want to talk through what happened before deciding what to do next?"
            )
        if emotion == "lonely":
            return (
                f"That sounds lonely and hard.{extra_context} "
                f"{prefix} You don’t have to sit with it by yourself right now. Want to tell me more?"
            )
        if emotion == "excited":
            return (
                f"I can feel the energy in that!{extra_context} "
                f"This sounds really meaningful to you. What are you most excited about?"
            )

        if support_pref == "direct":
            return f"{prefix} Tell me what happened, and we’ll sort it out together."
        return f"{prefix} Tell me a little more, and we’ll figure it out together."

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    memory_block = "\n".join(f"- {m}" for m in memories) if memories else "- No important long-term memories found."
    recent_block = "\n".join(f"- {c}" for c in recent_context) if recent_context else "- No recent conversation context found."
    past_block = "\n".join(f"- {c}" for c in relevant_past) if relevant_past else "- No relevant older conversation context found."
    preference_block = _build_user_preference_summary(user)

    user_prompt = f"""
Current user message:
{user_message}

Detected emotion:
{emotion}

Recent mood pattern:
{mood_pattern}

Desired support style:
{support_style}

User preferences:
{preference_block}

Recent conversation context:
{recent_block}

Relevant past conversation context:
{past_block}

Important long-term memories:
{memory_block}

Write one natural, human-friendly reply for spoken conversation.
Keep it supportive, contextual, short, emotionally appropriate, easy to say out loud,
and aligned with the user's preferred tone and support style.
Do not force coping suggestions unless they fit naturally.
""".strip()

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=220,
        system=build_system_prompt(),
        messages=[
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    parts = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)

    final_text = " ".join(parts).strip()

    if not final_text:
        final_text = "I’m here with you. Tell me a little more."

    return final_text