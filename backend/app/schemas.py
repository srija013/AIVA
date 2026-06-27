import re
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

    personality_type: Optional[str] = None
    coping_preferences: List[str] = []
    disliked_support_styles: List[str] = []
    preferred_response_tone: Optional[str] = None
    support_preference: Optional[str] = None

    likes_breathing: bool = True
    likes_games: bool = False
    likes_drawing: bool = False
    likes_journaling: bool = False
    likes_music: bool = False
    likes_grounding: bool = True

    favorite_movie: Optional[str] = None
    favorite_song: Optional[str] = None
    favorite_activity: Optional[str] = None
    comfort_activity: Optional[str] = None
    interests: List[str] = []
    movie_genres: List[str] = []
    music_genres: List[str] = []
    stress_response_style: Optional[str] = None
    active_time: Optional[str] = None
    emotional_support_preference: Optional[str] = None
    focus_areas: List[str] = []
    favorite_food: Optional[str] = None
    favorite_place_to_relax: Optional[str] = None
    favorite_hobby: Optional[str] = None
    favorite_person_to_talk_to: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must be at least 2 characters long")
        if len(value) > 50:
            raise ValueError("Name must be less than 50 characters")
        if not re.fullmatch(r"[A-Za-z][A-Za-z\s'.-]*", value):
            raise ValueError("Name contains invalid characters")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return value

    @field_validator(
        "favorite_movie",
        "favorite_song",
        "favorite_activity",
        "comfort_activity",
        mode="before",
    )
    @classmethod
    def clean_optional_text(cls, value):
        if value is None:
            return None
        value = str(value).strip()
        return value if value else None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user_id: str
    name: str
    email: str
    message: str


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    emotion: str
    sentiment_score: float
    emotional_intensity: float
    analysis_weight: float
    is_meaningful_for_analysis: bool
    mood_pattern: str
    dominant_recent_emotion: str
    recommendations: list[str]
    relief_tools: list[str]
    memories_used: list[str]
    recent_context_used: list[str]
    relevant_past_used: list[str]


class SpeakRequest(BaseModel):
    text: str


class UpdateProfileRequest(BaseModel):
    personality_type: Optional[str] = None
    coping_preferences: Optional[List[str]] = None
    disliked_support_styles: Optional[List[str]] = None
    preferred_response_tone: Optional[str] = None
    support_preference: Optional[str] = None

    likes_breathing: Optional[bool] = None
    likes_games: Optional[bool] = None
    likes_drawing: Optional[bool] = None
    likes_journaling: Optional[bool] = None
    likes_music: Optional[bool] = None
    likes_grounding: Optional[bool] = None

    favorite_movie: Optional[str] = None
    favorite_song: Optional[str] = None
    favorite_activity: Optional[str] = None
    comfort_activity: Optional[str] = None
    interests: Optional[List[str]] = None
    movie_genres: Optional[List[str]] = None
    music_genres: Optional[List[str]] = None
    stress_response_style: Optional[str] = None
    active_time: Optional[str] = None
    emotional_support_preference: Optional[str] = None
    focus_areas: Optional[List[str]] = None
    favorite_food: Optional[str] = None
    favorite_place_to_relax: Optional[str] = None
    favorite_hobby: Optional[str] = None
    favorite_person_to_talk_to: Optional[str] = None


class ActivityFeedbackRequest(BaseModel):
    user_id: str
    tool_name: str
    helped: bool = True
    notes: Optional[str] = None


class MoodCheckinRequest(BaseModel):
    user_id: str
    mood: str
    note: Optional[str] = None


class JournalEntryRequest(BaseModel):
    user_id: str
    mode: str = "free_write"
    title: Optional[str] = None
    content: str