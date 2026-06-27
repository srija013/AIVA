import random


BREATHING_STEPS = [
    "Let’s take a slow breath together.",
    "Inhale slowly… 1… 2… 3… 4",
    "Hold… 1… 2… 3… 4",
    "Exhale slowly… 1… 2… 3… 4… 5… 6",
    "That’s good. Let’s do one more if you want.",
]

GROUNDING_STEPS = [
    "Let’s ground for a moment.",
    "Name 5 things you can see.",
    "Now 4 things you can feel.",
    "Now 3 things you can hear.",
    "Take one slow breath and come back to the present.",
]

JOURNALING_PROMPTS = [
    "What feels heaviest right now?",
    "What happened just before this feeling got stronger?",
    "What do you need most right now?",
    "What would you say to a friend feeling this way?",
]

DRAWING_PROMPTS = [
    "Try drawing your mood using only shapes.",
    "Doodle without worrying how it looks.",
    "Use color to show how today feels.",
]

GAME_PROMPTS = [
    "A quick calming game might help you reset for a minute.",
    "Try a short focus game to shift your mind gently.",
]

MUSIC_PROMPTS = [
    "Try calming music or rain sounds for a minute.",
    "A soft instrumental track might help you settle.",
]

REFLECTION_PROMPTS = [
    "What do you think is causing this feeling?",
    "When did this start?",
    "What usually helps you in situations like this?",
    "What’s one small thing that might make this easier right now?",
]


def get_guided_action(emotion, relief_tools=None):
    relief_tools = relief_tools or []

    if "breathing" in relief_tools and emotion in ["anxious", "stressed"]:
        return {
            "tool": "breathing",
            "steps": BREATHING_STEPS,
        }

    if "grounding" in relief_tools and emotion in ["anxious", "stressed", "angry"]:
        return {
            "tool": "grounding",
            "steps": GROUNDING_STEPS,
        }

    if "journaling" in relief_tools and emotion in ["sad", "lonely"]:
        return {
            "tool": "journaling",
            "steps": [random.choice(JOURNALING_PROMPTS)],
        }

    if "drawing" in relief_tools:
        return {
            "tool": "drawing",
            "steps": [random.choice(DRAWING_PROMPTS)],
        }

    if "games" in relief_tools:
        return {
            "tool": "games",
            "steps": [random.choice(GAME_PROMPTS)],
        }

    if "music" in relief_tools:
        return {
            "tool": "music",
            "steps": [random.choice(MUSIC_PROMPTS)],
        }

    return {
        "tool": "reflection",
        "steps": [random.choice(REFLECTION_PROMPTS)],
    }


def get_reflection_prompt():
    return random.choice(REFLECTION_PROMPTS)


def get_relief_tool_catalog():
    return [
        {
            "id": "breathing",
            "title": "Breathing Reset",
            "description": "A short guided breathing exercise for stress and anxiety.",
        },
        {
            "id": "grounding",
            "title": "Grounding Exercise",
            "description": "A quick sensory grounding activity to help you settle.",
        },
        {
            "id": "journaling",
            "title": "Reflection Prompt",
            "description": "A gentle writing prompt to help express what you feel.",
        },
        {
            "id": "drawing",
            "title": "Drawing Relief",
            "description": "A doodle prompt for emotional release and calm.",
        },
        {
            "id": "games",
            "title": "Mini Reset Game",
            "description": "A short focus-based activity for distraction and reset.",
        },
        {
            "id": "music",
            "title": "Music Prompt",
            "description": "A suggestion to use calming sound or instrumental music.",
        },
    ]