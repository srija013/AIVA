from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app.models import (
    User,
    Conversation,
    Memory,
    EmotionLog,
    ActivityLog,
    MoodCheckin,
    JournalEntry,
    AvatarConfig,
)
from app.schemas import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    ChatRequest,
    ChatResponse,
    SpeakRequest,
    UpdateProfileRequest,
    ActivityFeedbackRequest,
    MoodCheckinRequest,
    JournalEntryRequest,
)
from app.auth import hash_password, verify_password
from app.emotion import detect_emotion_details
from app.memory import should_store_as_memory, save_memory, retrieve_relevant_memories
from app.context_retriever import get_recent_conversations, get_relevant_past_conversations
from app.chatbot import generate_reply
from app.voice_clone import clone_voice_elevenlabs, synthesize_with_cloned_voice
from app.recommendation import (
    get_recommendations,
    should_show_recommendations,
    get_relief_tools,
)
from app.mood_pattern import classify_mood_pattern
from app.safety import detect_crisis, get_crisis_response

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Companion Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AvatarConfigRequest(BaseModel):
    face_shape: Optional[str] = "oval"
    skin_tone: Optional[str] = "#F5C5A3"
    hair_style: Optional[str] = "long"
    hair_color: Optional[str] = "#3B2314"
    eye_style: Optional[str] = "normal"
    accessory: Optional[str] = "none"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _csv_join(items: list[str]) -> str:
    return ",".join(items) if items else ""


def _mood_score_from_emotion(emotion: str) -> float:
    mapping = {
        "happy": 0.85,
        "excited": 0.90,
        "neutral": 0.55,
        "sad": 0.30,
        "lonely": 0.28,
        "stressed": 0.35,
        "anxious": 0.32,
        "angry": 0.25,
        "critical": 0.10,
    }
    return mapping.get(emotion, 0.50)


def _checkin_score(mood: str) -> float:
    mapping = {
        "amazing": 0.92,
        "good": 0.75,
        "okay": 0.55,
        "down": 0.30,
        "need_support": 0.20,
    }
    return mapping.get(mood, 0.55)


def _build_daily_points(db: Session, user_id: str, days: int = 7):
    today = datetime.utcnow().date()
    start = today - timedelta(days=days - 1)

    emotion_logs = (
        db.query(EmotionLog)
        .filter(EmotionLog.user_id == user_id)
        .all()
    )
    mood_checkins = (
        db.query(MoodCheckin)
        .filter(MoodCheckin.user_id == user_id)
        .all()
    )

    grouped = defaultdict(lambda: {
        "emotion_scores": [],
        "emotions": [],
        "intensities": [],
        "meaningful": 0,
        "checkin_scores": [],
        "checkin_moods": [],
    })

    for log in emotion_logs:
        d = log.created_at.date()
        if d < start or d > today:
            continue
        grouped[d]["emotion_scores"].append(_mood_score_from_emotion(log.detected_emotion))
        grouped[d]["emotions"].append(log.detected_emotion)
        grouped[d]["intensities"].append(float(log.emotional_intensity or 0.0))
        if bool(log.is_meaningful_for_analysis):
            grouped[d]["meaningful"] += 1

    for checkin in mood_checkins:
        d = checkin.created_at.date()
        if d < start or d > today:
            continue
        grouped[d]["checkin_scores"].append(float(checkin.mood_score))
        grouped[d]["checkin_moods"].append(checkin.mood)

    points = []
    for i in range(days):
        d = start + timedelta(days=i)
        bucket = grouped[d]

        all_scores = bucket["emotion_scores"] + bucket["checkin_scores"]
        score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.50

        emotion_candidates = bucket["emotions"] + bucket["checkin_moods"]
        dominant = Counter(emotion_candidates).most_common(1)[0][0] if emotion_candidates else "neutral"

        if score >= 0.80:
            label = "Great"
        elif score >= 0.65:
            label = "Good"
        elif score >= 0.50:
            label = "Okay"
        elif score >= 0.35:
            label = "Low"
        else:
            label = "Need care"

        avg_intensity = round(sum(bucket["intensities"]) / len(bucket["intensities"]), 2) if bucket["intensities"] else 0.0

        points.append({
            "date": str(d),
            "day": d.strftime("%a"),
            "dominant_emotion": dominant,
            "mood_score": score,
            "label": label,
            "average_intensity": avg_intensity,
            "meaningful_count": bucket["meaningful"],
        })

    return points


def _build_analytics_summary(points: list[dict]):
    if not points:
        return {
            "trend_label": "Stable",
            "streak_days": 0,
            "best_day": "N/A",
            "worst_day": "N/A",
            "average_mood_label": "Okay",
            "average_mood_score": 0.50,
            "weekly_insight": "No analytics data yet.",
        }

    scores = [p["mood_score"] for p in points]
    avg_score = round(sum(scores) / len(scores), 2)
    first_avg = sum(scores[:3]) / max(1, len(scores[:3]))
    last_avg = sum(scores[-3:]) / max(1, len(scores[-3:]))

    if last_avg - first_avg > 0.08:
        trend = "Improving"
    elif first_avg - last_avg > 0.08:
        trend = "Needs care"
    else:
        trend = "Stable"

    positive_streak = 0
    for p in reversed(points):
        if p["mood_score"] >= 0.50:
            positive_streak += 1
        else:
            break

    best_day = max(points, key=lambda x: x["mood_score"])["day"]
    worst_day = min(points, key=lambda x: x["mood_score"])["day"]

    if avg_score >= 0.80:
        avg_label = "Bright"
    elif avg_score >= 0.65:
        avg_label = "Good"
    elif avg_score >= 0.50:
        avg_label = "Steady"
    elif avg_score >= 0.35:
        avg_label = "Heavy"
    else:
        avg_label = "Low"

    if trend == "Improving":
        insight = "Your mood has been improving across the week. Later days look steadier than earlier ones, which suggests recent routines may be helping."
    elif trend == "Needs care":
        insight = "This week looks emotionally heavier overall. There are more low points than steady ones, so a gentler pace and lower-pressure support may help."
    else:
        insight = "Your week looks relatively steady overall. There are small shifts, but no major swing across the trend."

    return {
        "trend_label": trend,
        "streak_days": positive_streak,
        "best_day": best_day,
        "worst_day": worst_day,
        "average_mood_label": avg_label,
        "average_mood_score": avg_score,
        "weekly_insight": insight,
    }


def _build_for_you(user, current_mood: str):
    cards = []

    favorite_movie = (getattr(user, "favorite_movie", None) or "").strip()
    favorite_song = (getattr(user, "favorite_song", None) or "").strip()
    favorite_activity = (getattr(user, "favorite_activity", None) or "").strip()
    comfort_activity = (getattr(user, "comfort_activity", None) or "").strip()

    def add(title, subtitle, tag, action_type, priority):
        cards.append({
            "title": title,
            "subtitle": subtitle,
            "tag": tag,
            "action_type": action_type,
            "priority": priority,
        })

    if current_mood in {"down", "need_support"}:
        add(
            "Talk to AIVA",
            "You seem emotionally heavy today. A short check-in may help.",
            "Support",
            "chat",
            1,
        )
        add(
            "Take a breathing reset",
            "A short guided breathing pause may help reduce the emotional pressure a little.",
            "Breathing",
            "breathing",
            2,
        )
        add(
            "Write it out",
            "A few honest lines may help clear your head without pressure.",
            "Journal",
            "journal",
            3,
        )
        add(
            "Play the soft swipe game",
            "A gentle focus activity may help when your thoughts feel crowded.",
            "Game",
            "game",
            4,
        )
        if favorite_song:
            add(
                "Play your comfort song",
                f"{favorite_song} may help soften the moment.",
                "Music",
                "music",
                5,
            )
        else:
            add(
                "Try calming music",
                "A soft soundtrack may help you slow the moment down.",
                "Music",
                "music",
                5,
            )
        if comfort_activity:
            add(
                "Do one comforting thing",
                f"{comfort_activity} may be a gentler next step than pushing yourself.",
                "Comfort",
                "comfort",
                6,
            )

    elif current_mood in {"amazing", "good"}:
        add(
            "Capture the feeling",
            "A short talk can help you hold onto what feels good today.",
            "Talk",
            "chat",
            1,
        )
        add(
            "Take a calm breath",
            "A tiny breathing pause can help you stay present in the moment.",
            "Breathing",
            "breathing",
            2,
        )
        add(
            "Journal a little",
            "Write down what is making today feel lighter.",
            "Journal",
            "journal",
            3,
        )
        add(
            "Play the soft swipe game",
            "A soothing focus break that keeps the mood gentle.",
            "Game",
            "game",
            4,
        )
        if favorite_activity:
            add(
                "Spend time on what you enjoy",
                f"{favorite_activity} could help keep the day feeling warm and steady.",
                "Enjoyment",
                "activity",
                5,
            )
        if favorite_song:
            add(
                "Keep the vibe going",
                f"Put on {favorite_song} and let the good mood stay with you a little longer.",
                "Music",
                "music",
                6,
            )

    else:
        add(
            "Talk a little",
            "A small check-in may help you understand today more clearly.",
            "Support",
            "chat",
            1,
        )
        add(
            "Try a short breathing pause",
            "A tiny breathing reset can help steady the day.",
            "Breathing",
            "breathing",
            2,
        )
        add(
            "Journal gently",
            "A few lines may help you organize what’s been sitting in your mind.",
            "Journal",
            "journal",
            3,
        )
        add(
            "Play the soft swipe game",
            "A soft focus reset for when you want a little mental space.",
            "Game",
            "game",
            4,
        )
        if favorite_movie:
            add(
                "Choose something familiar",
                f"Watching {favorite_movie} later could be a small comfort for the evening.",
                "Comfort",
                "movie",
                5,
            )
        else:
            add(
                "Soft music",
                "A calm soundtrack can help keep the day feeling lighter.",
                "Music",
                "music",
                5,
            )

    cards.sort(key=lambda x: x["priority"])

    if current_mood == "need_support":
        pro_tip = "Start with the easiest supportive thing. You do not need to do everything at once."
    elif current_mood == "down":
        pro_tip = "One kind action is enough for now. Choose comfort over pressure."
    elif current_mood in {"good", "amazing"}:
        pro_tip = "You do not need to maximize a good mood. Protecting it gently is enough."
    else:
        pro_tip = "Not every helpful thing has to be big. Small support still matters."

    return {
        "current_mood": current_mood,
        "cards": cards,
        "pro_tip": pro_tip,
    }


def _build_profile_stats(db: Session, user_id: str):
    mood_checkins = db.query(MoodCheckin).filter(MoodCheckin.user_id == user_id).all()
    journals = db.query(JournalEntry).filter(JournalEntry.user_id == user_id).all()
    activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
        .all()
    )

    checkin_days = sorted({m.created_at.date() for m in mood_checkins}, reverse=True)
    streak = 0
    today = datetime.utcnow().date()
    for i, d in enumerate(checkin_days):
        if d == today - timedelta(days=i):
            streak += 1
        else:
            break

    activity_counts = Counter([a.tool_name for a in activities])

    achievements = []
    if streak >= 3:
        achievements.append("3-Day Streak")
    if streak >= 7:
        achievements.append("7-Day Streak")
    if len(journals) >= 1:
        achievements.append("Journal Starter")
    if len(journals) >= 10:
        achievements.append("Journal Master")
    if len(mood_checkins) >= 10:
        achievements.append("Mood Tracker")
    if activity_counts.get("music", 0) >= 3:
        achievements.append("Soft Reset")

    recent_activity = [
        {
            "title": a.tool_name,
            "helped": a.helped,
            "notes": a.notes,
            "created_at": a.created_at.isoformat(),
        }
        for a in activities
    ]

    return {
        "streak": streak,
        "checkins": len(mood_checkins),
        "journal_entries": len(journals),
        "breathing_sessions": activity_counts.get("breathing", 0),
        "music_sessions": activity_counts.get("music", 0),
        "doodle_sessions": activity_counts.get("drawing", 0),
        "achievements": achievements,
        "recent_activity": recent_activity,
    }


@app.get("/")
def root():
    return {"message": "AI Companion Backend Running"}


@app.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=request.name,
        email=request.email,
        password_hash=hash_password(request.password),
        personality_type=request.personality_type,
        coping_preferences=_csv_join(request.coping_preferences),
        disliked_support_styles=_csv_join(request.disliked_support_styles),
        preferred_response_tone=request.preferred_response_tone,
        support_preference=request.support_preference,
        likes_breathing=request.likes_breathing,
        likes_games=request.likes_games,
        likes_drawing=request.likes_drawing,
        likes_journaling=request.likes_journaling,
        likes_music=request.likes_music,
        likes_grounding=request.likes_grounding,
        favorite_movie=request.favorite_movie,
        favorite_song=request.favorite_song,
        favorite_activity=request.favorite_activity,
        comfort_activity=request.comfort_activity,
        interests=_csv_join(request.interests),
        movie_genres=_csv_join(request.movie_genres),
        music_genres=_csv_join(request.music_genres),
        stress_response_style=request.stress_response_style,
        active_time=request.active_time,
        emotional_support_preference=request.emotional_support_preference,
        focus_areas=_csv_join(request.focus_areas),
        favorite_food=request.favorite_food,
        favorite_place_to_relax=request.favorite_place_to_relax,
        favorite_hobby=request.favorite_hobby,
        favorite_person_to_talk_to=request.favorite_person_to_talk_to,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return AuthResponse(
        user_id=str(new_user.id),
        name=new_user.name,
        email=new_user.email,
        message="Registration successful",
    )


@app.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return AuthResponse(
        user_id=str(user.id),
        name=user.name,
        email=user.email,
        message="Login successful",
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    emotion_details = detect_emotion_details(request.message)
    emotion = emotion_details["emotion"]
    sentiment_score = emotion_details["sentiment_score"]
    emotional_intensity = emotion_details["emotional_intensity"]
    analysis_weight = emotion_details["analysis_weight"]
    is_meaningful_for_analysis = emotion_details["is_meaningful_for_analysis"]

    recent_context = get_recent_conversations(db=db, user_id=request.user_id, limit=4)
    relevant_past = get_relevant_past_conversations(db=db, user_id=request.user_id, message=request.message, limit=3)
    memories_used = retrieve_relevant_memories(db=db, user_id=request.user_id, message=request.message, limit=3)

    emotion_log = EmotionLog(
        user_id=request.user_id,
        message_text=request.message,
        detected_emotion=emotion,
        sentiment_score=sentiment_score,
        emotional_intensity=emotional_intensity,
        analysis_weight=analysis_weight,
        is_meaningful_for_analysis=is_meaningful_for_analysis,
        trigger_recommendation=False,
    )
    db.add(emotion_log)
    db.commit()
    db.refresh(emotion_log)

    if detect_crisis(request.message):
        reply = get_crisis_response()
        conversation = Conversation(
            user_id=request.user_id,
            user_text=request.message,
            ai_text=reply,
            emotion="critical",
            sentiment_score=-1.0,
            emotional_intensity=1.0,
            analysis_weight=2.0,
            is_meaningful_for_analysis=True,
        )
        db.add(conversation)
        db.commit()

        if should_store_as_memory(request.message, "critical"):
            save_memory(db=db, user_id=request.user_id, message=request.message, emotion="critical")

        return ChatResponse(
            reply=reply,
            emotion="critical",
            sentiment_score=-1.0,
            emotional_intensity=1.0,
            analysis_weight=2.0,
            is_meaningful_for_analysis=True,
            mood_pattern="crisis",
            dominant_recent_emotion="critical",
            recommendations=[],
            relief_tools=[],
            memories_used=memories_used,
            recent_context_used=recent_context,
            relevant_past_used=relevant_past,
        )

    recent_logs = (
        db.query(EmotionLog)
        .filter(EmotionLog.user_id == request.user_id)
        .order_by(EmotionLog.created_at.desc())
        .limit(8)
        .all()
    )
    recent_logs = list(reversed(recent_logs))
    recent_emotions = [log.detected_emotion for log in recent_logs]
    recent_scores = [log.sentiment_score for log in recent_logs]
    recent_weights = [float(getattr(log, "analysis_weight", 0.1) or 0.1) for log in recent_logs]
    recent_meaningful = [bool(getattr(log, "is_meaningful_for_analysis", False)) for log in recent_logs]

    pattern_info = classify_mood_pattern(
        emotions=recent_emotions,
        sentiment_scores=recent_scores,
        analysis_weights=recent_weights,
        meaningful_flags=recent_meaningful,
    )

    mood_pattern = str(pattern_info["pattern"])
    dominant_recent_emotion = str(pattern_info["dominant_emotion"])
    relief_tools = get_relief_tools(user=user, emotion=emotion, pattern=mood_pattern)

    recommendations = []
    show_recs = should_show_recommendations(
        message=request.message,
        current_emotion=emotion,
        emotional_intensity=emotional_intensity,
        sentiment_score=sentiment_score,
        pattern=mood_pattern,
        is_meaningful_for_analysis=is_meaningful_for_analysis,
    )
    if show_recs:
        recommendations = get_recommendations(
            user=user,
            pattern=mood_pattern,
            relief_tools=relief_tools,
            emotion=emotion,
            limit=3,
        )

    emotion_log.trigger_recommendation = show_recs
    db.commit()

    reply = generate_reply(
        user_message=request.message,
        emotion=emotion,
        memories=memories_used,
        recent_context=recent_context,
        relevant_past=relevant_past,
        mood_pattern=mood_pattern,
        user=user,
    )

    conversation = Conversation(
        user_id=request.user_id,
        user_text=request.message,
        ai_text=reply,
        emotion=emotion,
        sentiment_score=sentiment_score,
        emotional_intensity=emotional_intensity,
        analysis_weight=analysis_weight,
        is_meaningful_for_analysis=is_meaningful_for_analysis,
    )
    db.add(conversation)
    db.commit()

    if should_store_as_memory(request.message, emotion):
        save_memory(db=db, user_id=request.user_id, message=request.message, emotion=emotion)

    return ChatResponse(
        reply=reply,
        emotion=emotion,
        sentiment_score=sentiment_score,
        emotional_intensity=emotional_intensity,
        analysis_weight=analysis_weight,
        is_meaningful_for_analysis=is_meaningful_for_analysis,
        mood_pattern=mood_pattern,
        dominant_recent_emotion=dominant_recent_emotion,
        recommendations=recommendations,
        relief_tools=relief_tools,
        memories_used=memories_used,
        recent_context_used=recent_context,
        relevant_past_used=relevant_past,
    )


@app.post("/activity-feedback")
def activity_feedback(request: ActivityFeedbackRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    log = ActivityLog(
        user_id=request.user_id,
        tool_name=request.tool_name,
        helped=request.helped,
        notes=request.notes,
    )
    db.add(log)
    db.commit()

    return {"message": "Activity feedback saved"}


@app.post("/mood-checkin")
def mood_checkin(request: MoodCheckinRequest, db: Session = Depends(get_db)):
    mood = request.mood.strip().lower()
    entry = MoodCheckin(
        user_id=request.user_id,
        mood=mood,
        mood_score=_checkin_score(mood),
        note=request.note,
    )
    db.add(entry)
    db.commit()
    return {"message": "Mood check-in saved"}


@app.post("/journal")
def journal_entry(request: JournalEntryRequest, db: Session = Depends(get_db)):
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Journal content cannot be empty")

    entry = JournalEntry(
        user_id=request.user_id,
        mode=request.mode,
        title=request.title,
        content=request.content.strip(),
    )
    db.add(entry)
    db.commit()

    if should_store_as_memory(request.content, "neutral"):
        save_memory(db=db, user_id=request.user_id, message=request.content, emotion="neutral")

    return {"message": "Journal saved"}


@app.put("/user-profile/{user_id}")
def update_user_profile(user_id: str, request: UpdateProfileRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.personality_type is not None:
        user.personality_type = request.personality_type
    if request.coping_preferences is not None:
        user.coping_preferences = _csv_join(request.coping_preferences)
    if request.disliked_support_styles is not None:
        user.disliked_support_styles = _csv_join(request.disliked_support_styles)
    if request.preferred_response_tone is not None:
        user.preferred_response_tone = request.preferred_response_tone
    if request.support_preference is not None:
        user.support_preference = request.support_preference
    if request.likes_breathing is not None:
        user.likes_breathing = request.likes_breathing
    if request.likes_games is not None:
        user.likes_games = request.likes_games
    if request.likes_drawing is not None:
        user.likes_drawing = request.likes_drawing
    if request.likes_journaling is not None:
        user.likes_journaling = request.likes_journaling
    if request.likes_music is not None:
        user.likes_music = request.likes_music
    if request.likes_grounding is not None:
        user.likes_grounding = request.likes_grounding
    if request.favorite_movie is not None:
        user.favorite_movie = request.favorite_movie
    if request.favorite_song is not None:
        user.favorite_song = request.favorite_song
    if request.favorite_activity is not None:
        user.favorite_activity = request.favorite_activity
    if request.comfort_activity is not None:
        user.comfort_activity = request.comfort_activity
    if request.interests is not None:
        user.interests = _csv_join(request.interests)
    if request.movie_genres is not None:
        user.movie_genres = _csv_join(request.movie_genres)
    if request.music_genres is not None:
        user.music_genres = _csv_join(request.music_genres)
    if request.stress_response_style is not None:
        user.stress_response_style = request.stress_response_style
    if request.active_time is not None:
        user.active_time = request.active_time
    if request.emotional_support_preference is not None:
        user.emotional_support_preference = request.emotional_support_preference
    if request.focus_areas is not None:
        user.focus_areas = _csv_join(request.focus_areas)
    if request.favorite_food is not None:
        user.favorite_food = request.favorite_food
    if request.favorite_place_to_relax is not None:
        user.favorite_place_to_relax = request.favorite_place_to_relax
    if request.favorite_hobby is not None:
        user.favorite_hobby = request.favorite_hobby
    if request.favorite_person_to_talk_to is not None:
        user.favorite_person_to_talk_to = request.favorite_person_to_talk_to

    db.commit()
    return {"message": "Profile updated successfully"}


@app.get("/user-profile/{user_id}")
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": str(user.id),
        "name": user.name,
        "email": user.email,
        "has_cloned_voice": user.cloned_voice_id is not None,
        "cloned_voice_id": user.cloned_voice_id,
        "personality_type": user.personality_type,
        "coping_preferences": user.coping_preferences.split(",") if user.coping_preferences else [],
        "disliked_support_styles": user.disliked_support_styles.split(",") if user.disliked_support_styles else [],
        "preferred_response_tone": user.preferred_response_tone,
        "support_preference": user.support_preference,
        "likes_breathing": user.likes_breathing,
        "likes_games": user.likes_games,
        "likes_drawing": user.likes_drawing,
        "likes_journaling": user.likes_journaling,
        "likes_music": user.likes_music,
        "likes_grounding": user.likes_grounding,
        "favorite_movie": user.favorite_movie,
        "favorite_song": user.favorite_song,
        "favorite_activity": user.favorite_activity,
        "comfort_activity": user.comfort_activity,
        "interests": user.interests.split(",") if user.interests else [],
        "movie_genres": user.movie_genres.split(",") if user.movie_genres else [],
        "music_genres": user.music_genres.split(",") if user.music_genres else [],
        "stress_response_style": user.stress_response_style,
        "active_time": user.active_time,
        "emotional_support_preference": user.emotional_support_preference,
        "focus_areas": user.focus_areas.split(",") if user.focus_areas else [],
        "favorite_food": user.favorite_food,
        "favorite_place_to_relax": user.favorite_place_to_relax,
        "favorite_hobby": user.favorite_hobby,
        "favorite_person_to_talk_to": user.favorite_person_to_talk_to,
    }


@app.get("/avatar-config/{user_id}")
def get_avatar_config(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    config = db.query(AvatarConfig).filter(AvatarConfig.user_id == user_id).first()

    if not config:
        return {
            "face_shape": "oval",
            "skin_tone": "#F5C5A3",
            "hair_style": "long",
            "hair_color": "#3B2314",
            "eye_style": "normal",
            "accessory": "none",
        }

    return {
        "face_shape": config.face_shape,
        "skin_tone": config.skin_tone,
        "hair_style": config.hair_style,
        "hair_color": config.hair_color,
        "eye_style": config.eye_style,
        "accessory": config.accessory,
    }


@app.put("/avatar-config/{user_id}")
def update_avatar_config(
    user_id: str,
    request: AvatarConfigRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    config = db.query(AvatarConfig).filter(AvatarConfig.user_id == user_id).first()

    if config:
        config.face_shape = request.face_shape or config.face_shape
        config.skin_tone = request.skin_tone or config.skin_tone
        config.hair_style = request.hair_style or config.hair_style
        config.hair_color = request.hair_color or config.hair_color
        config.eye_style = request.eye_style or config.eye_style
        config.accessory = request.accessory or config.accessory
        config.updated_at = datetime.utcnow()
    else:
        config = AvatarConfig(
            user_id=user_id,
            face_shape=request.face_shape or "oval",
            skin_tone=request.skin_tone or "#F5C5A3",
            hair_style=request.hair_style or "long",
            hair_color=request.hair_color or "#3B2314",
            eye_style=request.eye_style or "normal",
            accessory=request.accessory or "none",
        )
        db.add(config)

    db.commit()
    return {"message": "Avatar config saved"}


@app.get("/weekly-insights/{user_id}")
def get_weekly_insights(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.utcnow()
    week_ago = now - timedelta(days=6)

    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Conversation.created_at >= week_ago,
        )
        .order_by(Conversation.created_at.asc())
        .all()
    )

    mood_checkins = (
        db.query(MoodCheckin)
        .filter(
            MoodCheckin.user_id == user_id,
            MoodCheckin.created_at >= week_ago,
        )
        .order_by(MoodCheckin.created_at.asc())
        .all()
    )

    def mood_to_score(mood: str) -> float:
        mood = (mood or "").strip().lower()
        mapping = {
            "amazing": 5.0,
            "happy": 4.5,
            "good": 4.0,
            "okay": 3.0,
            "neutral": 3.0,
            "down": 2.0,
            "sad": 2.0,
            "need_support": 1.0,
            "need support": 1.0,
            "stressed": 2.0,
            "anxious": 2.0,
            "lonely": 2.0,
            "angry": 1.5,
        }
        return mapping.get(mood, 3.0)

    def score_to_label(score: float) -> str:
        if score >= 4.5:
            return "Amazing"
        if score >= 3.5:
            return "Good"
        if score >= 2.5:
            return "Okay"
        if score >= 1.5:
            return "Down"
        return "Need Support"

    def day_name(dt: datetime) -> str:
        return dt.strftime("%a")

    day_buckets = defaultdict(list)

    for item in conversations:
        emotion = (item.emotion or "").strip().lower()
        if emotion and emotion != "neutral":
            day_buckets[item.created_at.date()].append(mood_to_score(emotion))
        elif item.sentiment_score is not None:
            sentiment = float(item.sentiment_score)
            if sentiment > 0.2:
                day_buckets[item.created_at.date()].append(4.0)
            elif sentiment < -0.2:
                day_buckets[item.created_at.date()].append(2.0)
            else:
                day_buckets[item.created_at.date()].append(3.0)

    for item in mood_checkins:
        mood = (item.mood or "").strip().lower()
        if mood:
            day_buckets[item.created_at.date()].append(mood_to_score(mood))

    trend = []
    weekly_summary = []

    for i in range(7):
        day_dt = week_ago + timedelta(days=i)
        day_date = day_dt.date()
        values = day_buckets.get(day_date, [])

        if values:
            avg_score = round(sum(values) / len(values), 2)
            trend.append({
                "day": day_name(day_dt),
                "score": avg_score,
            })
            weekly_summary.append({
                "day": day_name(day_dt),
                "score": avg_score,
                "label": score_to_label(avg_score),
            })

    meaningful_logs_count = sum(len(v) for v in day_buckets.values())

    if meaningful_logs_count == 0:
        return {
            "meaningful_logs_count": 0,
            "trend_label": "",
            "streak": 0,
            "best_day": "",
            "average_mood_score": 0,
            "trend": [],
            "weekly_summary": [],
            "insight": "No analytics yet. Start chatting with AIVA to build your mood insights.",
        }

    average_mood_score = round(
        sum(item["score"] for item in trend) / len(trend), 2
    ) if trend else 0

    best_day = ""
    if weekly_summary:
        best_item = max(weekly_summary, key=lambda x: x["score"])
        best_day = best_item["day"]

    streak = 0
    for i in range(6, -1, -1):
        day_dt = week_ago + timedelta(days=i)
        if day_dt.date() in day_buckets and len(day_buckets[day_dt.date()]) > 0:
            streak += 1
        else:
            break

    if len(trend) >= 2:
        diff = trend[-1]["score"] - trend[0]["score"]
        if diff >= 0.75:
            trend_label = "Improving"
        elif diff <= -0.75:
            trend_label = "Lower"
        else:
            trend_label = "Stable"
    else:
        trend_label = "Building"

    if average_mood_score >= 4.0:
        insight = "Your week looks positive overall. Try to notice what has been helping and keep that rhythm going."
    elif average_mood_score >= 3.0:
        insight = "Your week looks relatively steady overall. There are small shifts, but no major swing across the trend."
    elif average_mood_score >= 2.0:
        insight = "This week seems a bit heavier. Gentle routines, rest, and small check-ins may help more than pressure."
    else:
        insight = "This week looks emotionally difficult. Keep things soft and simple, and use support tools when needed."

    return {
        "meaningful_logs_count": meaningful_logs_count,
        "trend_label": trend_label,
        "streak": streak,
        "best_day": best_day,
        "average_mood_score": average_mood_score,
        "trend": trend,
        "weekly_summary": weekly_summary,
        "insight": insight,
    }


@app.get("/analytics/{user_id}")
def analytics(user_id: str, db: Session = Depends(get_db)):
    points = _build_daily_points(db, user_id, 7)
    summary = _build_analytics_summary(points)
    return {
        **summary,
        "daily_mood_points": points,
    }


@app.get("/for-you/{user_id}")
def for_you(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    latest_checkin = (
        db.query(MoodCheckin)
        .filter(MoodCheckin.user_id == user_id)
        .order_by(MoodCheckin.created_at.desc())
        .first()
    )

    current_mood = latest_checkin.mood if latest_checkin else "okay"
    return _build_for_you(user, current_mood)


@app.get("/profile-stats/{user_id}")
def profile_stats(user_id: str, db: Session = Depends(get_db)):
    return _build_profile_stats(db, user_id)


@app.get("/memories/{user_id}")
def get_memories(user_id: str, db: Session = Depends(get_db)):
    memories = db.query(Memory).filter(Memory.user_id == user_id).order_by(Memory.created_at.desc()).all()
    return [
        {
            "id": memory.id,
            "text": memory.memory_text,
            "emotion": memory.emotion_tag,
            "type": memory.memory_type,
            "importance": memory.importance_score,
            "created_at": memory.created_at,
        }
        for memory in memories
    ]


@app.get("/conversations/{user_id}")
def get_conversations(user_id: str, db: Session = Depends(get_db)):
    conversations = db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).all()
    return [
        {
            "id": convo.id,
            "user_text": convo.user_text,
            "ai_text": convo.ai_text,
            "emotion": convo.emotion,
            "sentiment_score": convo.sentiment_score,
            "emotional_intensity": convo.emotional_intensity,
            "analysis_weight": convo.analysis_weight,
            "is_meaningful_for_analysis": convo.is_meaningful_for_analysis,
            "created_at": convo.created_at,
        }
        for convo in conversations
    ]


@app.get("/emotion_logs/{user_id}")
def get_emotion_logs(user_id: str, db: Session = Depends(get_db)):
    logs = db.query(EmotionLog).filter(EmotionLog.user_id == user_id).order_by(EmotionLog.created_at.desc()).all()
    return [
        {
            "id": log.id,
            "message_text": log.message_text,
            "detected_emotion": log.detected_emotion,
            "sentiment_score": log.sentiment_score,
            "emotional_intensity": log.emotional_intensity,
            "analysis_weight": log.analysis_weight,
            "is_meaningful_for_analysis": log.is_meaningful_for_analysis,
            "trigger_recommendation": log.trigger_recommendation,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@app.get("/journals/{user_id}")
def get_journals(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    journals = (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == user_id)
        .order_by(JournalEntry.created_at.desc())
        .all()
    )

    return {
        "count": len(journals),
        "journals": [
            {
                "id": journal.id,
                "title": journal.title or "",
                "mode": journal.mode or "free_write",
                "content": journal.content or "",
                "created_at": journal.created_at.isoformat() if journal.created_at else None,
            }
            for journal in journals
        ],
    }


@app.get("/journal/{journal_id}")
def get_single_journal(journal_id: int, db: Session = Depends(get_db)):
    journal = db.query(JournalEntry).filter(JournalEntry.id == journal_id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")

    return {
        "id": journal.id,
        "user_id": journal.user_id,
        "title": journal.title or "",
        "mode": journal.mode or "free_write",
        "content": journal.content or "",
        "created_at": journal.created_at.isoformat() if journal.created_at else None,
    }


@app.get("/activity-history/{user_id}")
def get_activity_history(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )

    return {
        "count": len(activities),
        "activities": [
            {
                "id": activity.id,
                "tool_name": activity.tool_name or "",
                "helped": bool(activity.helped) if activity.helped is not None else False,
                "notes": activity.notes or "",
                "created_at": activity.created_at.isoformat() if activity.created_at else None,
            }
            for activity in activities
        ],
    }


@app.get("/game-history/{user_id}")
def get_game_history(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    games = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.user_id == user_id,
            ActivityLog.tool_name == "game",
        )
        .order_by(ActivityLog.created_at.desc())
        .all()
    )

    return {
        "count": len(games),
        "games": [
            {
                "id": game.id,
                "tool_name": game.tool_name or "game",
                "helped": bool(game.helped) if game.helped is not None else False,
                "notes": game.notes or "",
                "created_at": game.created_at.isoformat() if game.created_at else None,
            }
            for game in games
        ],
    }


@app.get("/drawing-history/{user_id}")
def get_drawing_history(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    drawings = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.user_id == user_id,
            ActivityLog.tool_name == "drawing",
        )
        .order_by(ActivityLog.created_at.desc())
        .all()
    )

    return {
        "count": len(drawings),
        "drawings": [
            {
                "id": drawing.id,
                "tool_name": drawing.tool_name or "drawing",
                "helped": bool(drawing.helped) if drawing.helped is not None else False,
                "notes": drawing.notes or "",
                "created_at": drawing.created_at.isoformat() if drawing.created_at else None,
            }
            for drawing in drawings
        ],
    }


@app.get("/history-summary/{user_id}")
def get_history_summary(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    journal_count = db.query(JournalEntry).filter(JournalEntry.user_id == user_id).count()

    all_activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .all()
    )

    drawing_count = sum(1 for a in all_activities if (a.tool_name or "").lower() == "drawing")
    game_count = sum(1 for a in all_activities if (a.tool_name or "").lower() == "game")
    breathing_count = sum(1 for a in all_activities if (a.tool_name or "").lower() == "breathing")
    music_count = sum(1 for a in all_activities if (a.tool_name or "").lower() == "music")
    journaling_activity_count = sum(1 for a in all_activities if (a.tool_name or "").lower() == "journaling")

    return {
        "journals": journal_count,
        "drawing_sessions": drawing_count,
        "game_sessions": game_count,
        "breathing_sessions": breathing_count,
        "music_sessions": music_count,
        "journaling_activity_sessions": journaling_activity_count,
    }


@app.post("/voice-clone/{user_id}")
def clone_voice(user_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_bytes = file.file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        local_voice_path = clone_voice_elevenlabs(
            file_bytes=file_bytes,
            filename=file.filename or "voice_sample.wav",
            voice_name=f"{user.name}_voice_reference",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local voice setup failed: {str(e)}")

    user.cloned_voice_id = local_voice_path
    db.commit()

    return {
        "message": "Voice sample saved successfully",
        "voice_id": local_voice_path,
    }


@app.post("/speak/{user_id}")
def speak_with_cloned_voice(user_id: str, request: SpeakRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.cloned_voice_id:
        raise HTTPException(status_code=400, detail="No saved voice sample found for this user")

    try:
        audio_bytes = synthesize_with_cloned_voice(
            voice_id=user.cloned_voice_id,
            text=request.text,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech generation failed: {str(e)}")

    return Response(content=audio_bytes, media_type="audio/wav")