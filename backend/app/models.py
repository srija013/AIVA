from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    cloned_voice_id = Column(String, nullable=True)

    personality_type = Column(String, nullable=True)
    coping_preferences = Column(Text, nullable=True)
    disliked_support_styles = Column(Text, nullable=True)
    preferred_response_tone = Column(String, nullable=True)
    support_preference = Column(String, nullable=True)

    likes_breathing = Column(Boolean, default=True)
    likes_games = Column(Boolean, default=False)
    likes_drawing = Column(Boolean, default=False)
    likes_journaling = Column(Boolean, default=False)
    likes_music = Column(Boolean, default=False)
    likes_grounding = Column(Boolean, default=True)

    favorite_movie = Column(String, nullable=True)
    favorite_song = Column(String, nullable=True)
    favorite_activity = Column(String, nullable=True)
    comfort_activity = Column(String, nullable=True)
    interests = Column(Text, nullable=True)
    movie_genres = Column(Text, nullable=True)
    music_genres = Column(Text, nullable=True)
    stress_response_style = Column(String, nullable=True)
    active_time = Column(String, nullable=True)
    emotional_support_preference = Column(String, nullable=True)
    focus_areas = Column(Text, nullable=True)
    favorite_food = Column(String, nullable=True)
    favorite_place_to_relax = Column(String, nullable=True)
    favorite_hobby = Column(String, nullable=True)
    favorite_person_to_talk_to = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    user_text = Column(Text, nullable=False)
    ai_text = Column(Text, nullable=False)

    emotion = Column(String, default="neutral")
    sentiment_score = Column(Float, default=0.0)
    emotional_intensity = Column(Float, default=0.0)
    analysis_weight = Column(Float, default=0.1)
    is_meaningful_for_analysis = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    memory_text = Column(Text, nullable=False)
    memory_type = Column(String, default="semantic")
    importance_score = Column(Float, default=0.8)
    emotion_tag = Column(String, default="neutral")
    created_at = Column(DateTime, default=datetime.utcnow)


class EmotionLog(Base):
    __tablename__ = "emotion_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    message_text = Column(Text, nullable=False)

    detected_emotion = Column(String, nullable=False)
    sentiment_score = Column(Float, default=0.0)
    emotional_intensity = Column(Float, default=0.0)
    analysis_weight = Column(Float, default=0.1)
    is_meaningful_for_analysis = Column(Boolean, default=False)
    trigger_recommendation = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    tool_name = Column(String, nullable=False)
    helped = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MoodCheckin(Base):
    __tablename__ = "mood_checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    mood = Column(String, nullable=False)
    mood_score = Column(Float, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    mode = Column(String, default="free_write")
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AvatarConfig(Base):
    __tablename__ = "avatar_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)

    face_shape = Column(String, default="oval")
    skin_tone = Column(String, default="#F5C5A3")
    hair_style = Column(String, default="long")
    hair_color = Column(String, default="#3B2314")
    eye_style = Column(String, default="normal")
    accessory = Column(String, default="none")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)