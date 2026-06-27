# Voice AI Reimagined — Mobile Frontend

A Flutter-based mobile application for an emotion-aware AI voice companion. The app provides voice and text interaction, personalized conversations, mood tracking, journaling, relaxation tools, and long-term user engagement through an intuitive mobile interface.

> This repository contains only the Flutter frontend. The AI processing, authentication, conversation storage, and response generation are handled by a separate FastAPI backend.

---

## Features

### User Onboarding and Personalization

- User registration and login
- Personality selection
- User-interest selection
- Content preferences
- Favourite comfort activities
- Preferred emotional-support style
- Avatar customization

### AI Conversation

- Text-based chat interface
- Voice input through the device microphone
- Speech-to-text interaction
- Text-to-speech response playback
- Emotion-aware AI responses
- Personalized conversations based on user preferences
- Conversation-history viewing

### Mood and Wellness

- Mood logging
- Mood analytics dashboard
- Weekly emotional-trend tracking
- Personalized weekly recommendations
- Journaling and journal-history management
- Guided breathing exercises
- Relaxation activities and games

### User Dashboard

- Profile overview
- Activity statistics
- Quick actions
- User-preference management
- Mood summaries
- Personalized suggestions

---

## Technology Stack

- **Framework:** Flutter
- **Language:** Dart
- **Platforms:** Android and iOS
- **Development Tools:** Android Studio, Visual Studio Code
- **API Communication:** REST API integration
- **Voice Input:** Device microphone
- **Voice Output:** Text-to-Speech
- **Version Control:** Git and GitHub

---

## Application Flow

1. The user creates an account or logs in.
2. The user selects their personality, interests, preferences, and support style.
3. The application displays a personalized home dashboard.
4. The user interacts with the AI companion through text or voice.
5. The frontend sends the user’s message to the backend API.
6. The backend returns the AI response, detected emotion, and recommendations.
7. The application displays the response and optionally plays it as speech.
8. The user can view mood trends, conversation history, journal entries, and personalized wellness activities.

---

## Project Structure

```text
lib/
├── main.dart
├── models/
│   ├── user_model.dart
│   ├── message_model.dart
│   └── mood_model.dart
├── screens/
│   ├── authentication/
│   ├── onboarding/
│   ├── home/
│   ├── chat/
│   ├── mood/
│   ├── journal/
│   ├── relaxation/
│   └── profile/
├── services/
│   ├── api_service.dart
│   ├── speech_service.dart
│   └── storage_service.dart
├── widgets/
├── utils/
└── constants/
