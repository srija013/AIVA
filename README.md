# Voice AI Reimagined: A Mobile Companion

A Flutter-based mobile application that provides an emotion-aware and personalized AI companion through voice and text interaction.

The application allows users to communicate with an AI companion, track their emotional patterns, maintain journals, view mood analytics, receive personalized recommendations, and access relaxation activities. It connects to a FastAPI backend responsible for speech processing, emotion analysis, conversation memory, response generation, and data storage.

> This repository contains the **Flutter frontend application only**.  
> The FastAPI backend and AI-processing modules are maintained separately.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Application Workflow](#application-workflow)
- [Application Screens](#application-screens)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Backend Configuration](#backend-configuration)
- [Required Permissions](#required-permissions)
- [API Communication](#api-communication)
- [Running the Application](#running-the-application)
- [Building the Application](#building-the-application)
- [Testing](#testing)
- [Screenshots](#screenshots)
- [Privacy and Security](#privacy-and-security)
- [Limitations](#limitations)
- [Future Enhancements](#future-enhancements)
- [Contributors](#contributors)
- [Academic Information](#academic-information)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Project Overview

Most traditional voice assistants provide responses using only the current user input and limited short-term context. They often do not remember previous conversations, analyze emotional patterns over time, or personalize their responses according to the user's preferences.

**Voice AI Reimagined** addresses these limitations by providing a mobile AI companion capable of:

- Accepting text and voice input
- Maintaining conversation continuity
- Detecting emotions and sentiment
- Remembering useful information from previous interactions
- Generating personalized responses
- Tracking emotional patterns
- Providing mood insights and wellness activities
- Delivering responses through text and speech

The mobile frontend is developed using Flutter to provide a responsive and cross-platform user experience.

---

## Problem Statement

To develop a smart, voice-enabled AI companion with persistent conversational memory, emotion detection, adaptive response generation, mood tracking, and personalized user interaction.

---

## Objectives

The main objectives of the project are:

1. Develop a voice-enabled mobile AI companion.
2. Enable natural interaction through Speech-to-Text and Text-to-Speech.
3. provide emotion-aware and context-aware conversations.
4. Maintain conversation history and long-term user memory.
5. Personalize responses using user interests and preferences.
6. Track emotional patterns and generate weekly mood insights.
7. Provide journaling, breathing exercises, and relaxation activities.
8. Create an accessible and user-friendly Flutter interface.

---

## Key Features

### 1. User Authentication

- User account creation
- Secure login
- User profile management
- Persistent user sessions
- Personalized dashboard after login

### 2. Personalized Onboarding

During account setup, users can provide information that helps personalize their experience.

The onboarding process includes:

- Personality selection
- Interest selection
- Content preferences
- Favourite comfort activities
- Preferred emotional-support style
- Basic profile information
- Avatar selection and customization

### 3. Text-Based AI Conversation

The chat interface allows users to:

- Send text messages
- Receive AI-generated responses
- View detected emotions
- Receive personalized suggestions
- Continue previous conversations
- View timestamps and conversation history

### 4. Voice Interaction

The application supports voice-based communication through the device microphone.

The frontend:

1. Requests microphone permission.
2. Records or captures user speech.
3. Sends the audio or converted text to the backend.
4. Receives the AI-generated response.
5. Displays the response in the chat interface.
6. Plays the response through Text-to-Speech.

### 5. Emotion-Aware Responses

The backend analyzes the user's message and returns an emotion or sentiment result.

The frontend can display and use emotions such as:

- Happy
- Sad
- Stressed
- Anxious
- Angry
- Neutral
- Excited

The AI response is adapted according to the identified emotion, user preferences, recent conversations, and stored context.

### 6. Long-Term Conversation Memory

The application supports continuous and personalized conversations by connecting to a backend memory system.

The system can use:

- Previous conversations
- Important user preferences
- Repeated emotional patterns
- Personal interests
- Relevant past events
- Recent mood logs

This allows the AI companion to avoid treating every conversation as a completely new interaction.

### 7. Mood Analytics

The mood dashboard helps users understand their emotional patterns.

It includes:

- Daily mood records
- Weekly mood trends
- Frequently detected emotions
- Emotional summaries
- Mood-based insights
- Personalized recommendations

### 8. Weekly Recommendations

Recommendations may be generated using:

- Recent mood patterns
- User interests
- Favourite comfort activities
- Conversation history
- Selected support style

Possible recommendations include:

- Breathing exercises
- Journaling
- Relaxation activities
- Listening to music
- Taking a short break
- Speaking with a trusted person
- Performing a preferred comfort activity

### 9. Personal Journal

The journal module allows users to:

- Create journal entries
- Record thoughts and emotions
- View previous entries
- Track entry dates
- Maintain a private reflection history

### 10. Breathing Exercise

The guided breathing screen provides a simple relaxation activity.

It may include stages such as:

- Inhale
- Hold
- Exhale
- Repeat

The interface can use animations and timed instructions to guide the user.

### 11. Relaxation Activities

The application includes basic activities intended to improve user engagement and relaxation.

Examples include:

- Relaxation game
- Guided breathing
- Journaling
- Personalized comfort suggestions

### 12. Conversation History

Users can view previous interactions, including:

- User messages
- AI responses
- Conversation dates
- Detected emotions
- Previous recommendations

### 13. Avatar Customization

Users can personalize the visual appearance of their AI companion.

Possible options include:

- Avatar selection
- Character appearance
- Profile image
- Companion style
- Visual theme

### 14. User Dashboard

The home dashboard provides access to:

- AI chat
- Voice interaction
- Mood analytics
- Journal
- Relaxation activities
- Weekly recommendations
- Conversation history
- Profile settings
- Quick actions

---

## Technology Stack

### Frontend

| Technology | Purpose |
|---|---|
| Flutter | Cross-platform mobile application development |
| Dart | Programming language used by Flutter |
| Material Design | User-interface components and layouts |
| REST APIs | Communication with the FastAPI backend |
| Device Microphone | Capturing voice input |
| Text-to-Speech | Playing AI responses as speech |
| Git | Version control |
| GitHub | Repository hosting and collaboration |

### Connected Backend

The separate backend is developed using:

| Technology | Purpose |
|---|---|
| Python | Backend and AI processing |
| FastAPI | REST API development |
| SQLite | User, conversation, mood, and memory storage |
| Whisper | Speech-to-Text |
| gTTS or TTS engine | Converting responses to speech |
| DistilBERT | Text classification and emotion-related processing |
| DistilRoBERTa | Emotion or sentiment analysis |
| FLAN-T5 | Response-generation support |

The exact models and services may differ according to the deployed backend configuration.

---

## System Architecture

The application follows a frontend-backend architecture.

```text
┌─────────────────────────────────────────────┐
│           Flutter Mobile Frontend           │
│                                             │
│  Authentication   Dashboard   Profile       │
│  Chat Interface   Voice Input  Mood UI      │
│  Journal          Relaxation   History      │
└──────────────────────┬──────────────────────┘
                       │
                       │ REST API Requests
                       ▼
┌─────────────────────────────────────────────┐
│               FastAPI Backend               │
│                                             │
│  Authentication        Context Management   │
│  Speech Processing     Emotion Analysis     │
│  Response Generation   Recommendations      │
│  Memory Management     Mood Tracking        │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│               SQLite Database               │
│                                             │
│  Users              Conversations           │
│  Messages           Emotion Logs            │
│  Preferences        Journal Entries         │
│  Mood Records       Long-Term Memories      │
└─────────────────────────────────────────────┘
```

### Frontend Responsibilities

The Flutter application is responsible for:

- Displaying the user interface
- Collecting user input
- Capturing voice input
- Validating form data
- Sending requests to the backend
- Displaying AI responses
- Showing mood analytics
- Managing navigation
- Playing voice responses
- Handling loading and error states

### Backend Responsibilities

The backend is responsible for:

- User authentication
- Speech-to-Text processing
- Emotion and sentiment analysis
- Context retrieval
- Long-term memory management
- AI response generation
- Recommendation generation
- Conversation storage
- Mood-log management
- Journal storage
- Database operations

---

## Application Workflow

```text
User opens the application
          │
          ▼
User signs up or logs in
          │
          ▼
User completes preference-based onboarding
          │
          ▼
Home dashboard is displayed
          │
          ▼
User selects text or voice interaction
          │
          ▼
Frontend captures the user's input
          │
          ▼
Input is sent to the FastAPI backend
          │
          ▼
Backend performs emotion and sentiment analysis
          │
          ▼
Relevant previous conversations and memories are retrieved
          │
          ▼
A personalized AI response is generated
          │
          ▼
Response, emotion and recommendations are returned
          │
          ▼
Flutter frontend displays the result
          │
          ▼
Response may be played using Text-to-Speech
          │
          ▼
Mood analytics and conversation history are updated
```

---

## Application Screens

The frontend includes the following major screens.

### Authentication

- User registration
- User login
- Authentication error handling

### Onboarding

- Personality selection
- Interest selection
- Content-preference selection
- Favourite comfort activities
- Support-style selection

### Home

- Main dashboard
- Quick actions
- Personalized greeting
- Recent activity
- Mood summary

### Profile

- Profile overview
- Activity statistics
- User preferences
- Avatar customization

### AI Interaction

- Chat interface
- Voice-interaction screen
- AI-response display
- Emotion display
- Personalized suggestions

### Mood and Wellness

- Mood analytics
- Weekly emotional trend
- Weekly recommendations
- Personalized suggestions
- Breathing exercise
- Relaxation game

### Journal and History

- Create journal entry
- Journal history
- Conversation history
- Previous emotion records

---

## Project Structure

The following is a recommended Flutter project structure. Adjust it to match the actual folders in your repository.

```text
voice_ai_frontend/
│
├── android/
├── ios/
├── assets/
│   ├── images/
│   ├── icons/
│   ├── animations/
│   └── screenshots/
│
├── lib/
│   ├── main.dart
│   │
│   ├── config/
│   │   ├── api_config.dart
│   │   ├── app_routes.dart
│   │   └── app_theme.dart
│   │
│   ├── models/
│   │   ├── user_model.dart
│   │   ├── message_model.dart
│   │   ├── conversation_model.dart
│   │   ├── mood_model.dart
│   │   ├── journal_model.dart
│   │   └── recommendation_model.dart
│   │
│   ├── screens/
│   │   ├── authentication/
│   │   │   ├── login_screen.dart
│   │   │   └── signup_screen.dart
│   │   │
│   │   ├── onboarding/
│   │   │   ├── personality_screen.dart
│   │   │   ├── interests_screen.dart
│   │   │   ├── preferences_screen.dart
│   │   │   ├── comfort_activities_screen.dart
│   │   │   └── support_style_screen.dart
│   │   │
│   │   ├── home/
│   │   │   └── home_screen.dart
│   │   │
│   │   ├── chat/
│   │   │   ├── chat_screen.dart
│   │   │   └── voice_interaction_screen.dart
│   │   │
│   │   ├── mood/
│   │   │   ├── mood_analytics_screen.dart
│   │   │   └── weekly_trend_screen.dart
│   │   │
│   │   ├── journal/
│   │   │   ├── journal_screen.dart
│   │   │   └── journal_history_screen.dart
│   │   │
│   │   ├── relaxation/
│   │   │   ├── breathing_screen.dart
│   │   │   └── relaxation_game_screen.dart
│   │   │
│   │   ├── history/
│   │   │   └── conversation_history_screen.dart
│   │   │
│   │   └── profile/
│   │       ├── profile_screen.dart
│   │       └── avatar_customization_screen.dart
│   │
│   ├── services/
│   │   ├── api_service.dart
│   │   ├── authentication_service.dart
│   │   ├── chat_service.dart
│   │   ├── mood_service.dart
│   │   ├── journal_service.dart
│   │   ├── speech_service.dart
│   │   └── storage_service.dart
│   │
│   ├── widgets/
│   │   ├── custom_button.dart
│   │   ├── custom_text_field.dart
│   │   ├── message_bubble.dart
│   │   ├── mood_card.dart
│   │   ├── recommendation_card.dart
│   │   └── loading_indicator.dart
│   │
│   └── utils/
│       ├── validators.dart
│       ├── constants.dart
│       └── helpers.dart
│
├── test/
├── .gitignore
├── pubspec.yaml
├── pubspec.lock
└── README.md
```

---

## Getting Started

### Prerequisites

Install the following tools before running the project:

- Flutter SDK
- Dart SDK
- Android Studio or Visual Studio Code
- Android SDK
- Android emulator or physical Android device
- Git
- Xcode for iOS development on macOS

Verify the Flutter installation:

```bash
flutter doctor
```

Resolve any issues reported by `flutter doctor` before continuing.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_FRONTEND_REPOSITORY.git
```

### 2. Enter the project directory

```bash
cd YOUR_FRONTEND_REPOSITORY
```

### 3. Install Flutter dependencies

```bash
flutter pub get
```

### 4. Check connected devices

```bash
flutter devices
```

### 5. Configure the backend URL

Update the backend base URL before running the application.

---

## Backend Configuration

Create or locate an API configuration file such as:

```text
lib/config/api_config.dart
```

Example:

```dart
class ApiConfig {
  static const String baseUrl = 'http://YOUR_BACKEND_ADDRESS:8000';
}
```

### Android Emulator

To connect an Android emulator to a backend running on the same computer:

```dart
static const String baseUrl = 'http://10.0.2.2:8000';
```

### Physical Android Device

Use the local IPv4 address of the computer running the backend:

```dart
static const String baseUrl = 'http://192.168.1.10:8000';
```

The phone and computer must normally be connected to the same network.

### Deployed Backend

For a publicly deployed backend:

```dart
static const String baseUrl = 'https://your-backend-domain.com';
```

Do not place private API keys, passwords, or authentication secrets directly inside the Flutter source code.

---

## Required Permissions

### Android

Open:

```text
android/app/src/main/AndroidManifest.xml
```

Add internet and microphone permissions:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

Depending on the implementation, additional permissions may be required for:

- Notifications
- Local file access
- Audio storage
- Camera or avatar-image selection

### iOS

Open:

```text
ios/Runner/Info.plist
```

Add a microphone usage description:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>This application requires microphone access for voice interaction with the AI companion.</string>
```

---

## API Communication

The frontend communicates with the backend using REST API requests.

The exact API routes depend on the backend implementation.

### Example Chat Request

```json
{
  "user_id": 1,
  "message": "I am feeling stressed about my exams."
}
```

### Example Chat Response

```json
{
  "reply": "It sounds like your exams are causing you stress. Would you like to try a short breathing exercise?",
  "emotion": "stressed",
  "sentiment": "negative",
  "recommendations": [
    "Try a breathing exercise",
    "Write a journal entry",
    "Take a short break"
  ]
}
```

### Example Flutter Request

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatService {
  final String baseUrl;

  ChatService({required this.baseUrl});

  Future<Map<String, dynamic>> sendMessage({
    required int userId,
    required String message,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/YOUR_CHAT_ENDPOINT'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'user_id': userId,
        'message': message,
      }),
    );

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }

    throw Exception(
      'Unable to send message. Server returned ${response.statusCode}.',
    );
  }
}
```

Replace `YOUR_CHAT_ENDPOINT` with the actual backend route.

### Error Handling

The frontend should handle:

- No internet connection
- Backend unavailable
- Invalid credentials
- Empty messages
- Microphone permission denied
- Speech-recognition failure
- API timeout
- Unexpected response format
- Failed Text-to-Speech playback

---

## Running the Application

Run the application on the default connected device:

```bash
flutter run
```

Run it on a particular device:

```bash
flutter run -d DEVICE_ID
```

Run in release mode:

```bash
flutter run --release
```

Check code for common issues:

```bash
flutter analyze
```

Format the Dart source code:

```bash
dart format .
```

---

## Building the Application

### Android APK

```bash
flutter build apk --release
```

The APK is generally generated at:

```text
build/app/outputs/flutter-apk/app-release.apk
```

### Android App Bundle

```bash
flutter build appbundle --release
```

The bundle is generally generated at:

```text
build/app/outputs/bundle/release/app-release.aab
```

### iOS

```bash
flutter build ios --release
```

An iOS build requires macOS and Xcode.

---

## Testing

Run all Flutter tests:

```bash
flutter test
```

Recommended frontend test cases include:

| Test Case | Expected Result |
|---|---|
| User enters valid login credentials | User is redirected to the dashboard |
| User enters invalid credentials | Appropriate error message is displayed |
| User submits an empty message | Message is not sent |
| User sends a valid text message | Loading state appears and AI response is displayed |
| User denies microphone permission | Permission error is shown |
| Backend is unavailable | Network error is displayed without crashing |
| Mood data is returned | Mood chart is rendered correctly |
| Journal entry is submitted | Entry appears in journal history |
| Conversation history is loaded | Previous conversations are displayed |
| User changes preferences | Updated preferences are reflected in the profile |
| User starts breathing exercise | Breathing animation and timer begin |
| User selects an avatar | Selected avatar appears in the profile |

---

## Screenshots

Create the following directory:

```text
assets/screenshots/
```

Add screenshots and update this section.

### Authentication and Onboarding

| Registration | Personality Selection | Interests |
|---|---|---|
| ![Registration](assets/screenshots/registration.png) | ![Personality](assets/screenshots/personality.png) | ![Interests](assets/screenshots/interests.png) |

### Dashboard and Chat

| Home Dashboard | AI Chat | Voice Interaction |
|---|---|---|
| ![Dashboard](assets/screenshots/dashboard.png) | ![Chat](assets/screenshots/chat.png) | ![Voice](assets/screenshots/voice.png) |

### Mood and Wellness

| Mood Analytics | Weekly Trend | Breathing Exercise |
|---|---|---|
| ![Mood Analytics](assets/screenshots/mood-analytics.png) | ![Weekly Trend](assets/screenshots/weekly-trend.png) | ![Breathing](assets/screenshots/breathing.png) |

### Journal and Profile

| Journal | Conversation History | Avatar Customization |
|---|---|---|
| ![Journal](assets/screenshots/journal.png) | ![History](assets/screenshots/history.png) | ![Avatar](assets/screenshots/avatar.png) |

Remove any screenshot references for files that have not yet been added.

---

## Privacy and Security

The application may process sensitive information such as:

- User messages
- Voice recordings
- Emotional states
- Journal entries
- Personal preferences
- Conversation history

Recommended security practices include:

- Use HTTPS for production API communication.
- Do not commit API keys or passwords.
- Do not commit real user databases.
- Do not include private conversation data in screenshots.
- Avoid storing raw passwords.
- Use secure authentication tokens.
- Request only necessary device permissions.
- Allow users to delete their data.
- Clearly explain how conversation and mood data are used.
- Avoid retaining raw audio longer than necessary.

Files such as the following should not be committed:

```text
.env
.env.*
*.jks
*.keystore
key.properties
local.properties
*.db
*.sqlite
*.sqlite3
```

---

## Limitations

Current limitations may include:

- Requires a stable internet connection for backend processing.
- Speech recognition may be affected by background noise.
- Accuracy may vary depending on accent and speaking style.
- Emotion detection may not always reflect the user's actual emotional state.
- Response quality depends on the connected AI model.
- Some features depend on the availability of the backend server.
- The application does not provide medical diagnosis.
- The application is not a replacement for professional mental-health services.

---

## Future Enhancements

Possible future improvements include:

- Multilingual voice interaction
- Improved emotion-detection models
- Real-time animated AI avatar
- Multiple companion personalities
- Multiple Text-to-Speech voices
- Better voice personalization
- Offline journaling support
- Offline mood logging
- Push notifications
- Daily wellness reminders
- Wearable-device integration
- IoT-device integration
- Dark mode
- Improved accessibility
- Advanced mood visualizations
- Secure cloud synchronization
- Account and data-deletion controls
- End-to-end encrypted conversations
- More relaxation games
- More advanced large language models
- Improved crisis-support resources

---

## Contributors

- **Kuntala Hasini**
- **Polu Varshitha**
- **Kethepalli Srija**

---

## Academic Information

This project was developed as part of the **Mini Project-1** requirement for the award of the degree of:

**Bachelor of Technology in Information Technology**

at:

**G. Narayanamma Institute of Technology and Science (For Women)**  
Hyderabad, Telangana, India

**Project Batch:** 24B03  
**Development Period:** January 2026 – May 2026  
**Internal Guide:** Dr. V. Sesha Bhargavi, Associate Professor, Department of Information Technology

---

## Disclaimer

Voice AI Reimagined is intended for educational purposes, general companionship, mood reflection, and basic emotional-wellness support.

It is not designed to:

- Diagnose mental-health conditions
- Provide medical advice
- Replace a psychologist, psychiatrist, counsellor, or doctor
- Provide emergency or crisis intervention

Users experiencing a medical or mental-health emergency should contact qualified professionals or local emergency services.

---

## License

This project was developed for academic purposes.

Before selecting an open-source license, confirm that all contributors agree to make the source code publicly reusable.

You may add an MIT License after receiving approval from all project contributors.

---

## Repository Description

Use the following description in the GitHub repository settings:

> Flutter frontend for an emotion-aware AI voice companion featuring personalized conversations, mood analytics, journaling, wellness activities, long-term interaction, and FastAPI backend integration.

---

## Suggested GitHub Topics

```text
flutter
dart
mobile-application
voice-assistant
artificial-intelligence
conversational-ai
speech-to-text
text-to-speech
emotion-detection
sentiment-analysis
mood-tracking
mental-wellness
fastapi
rest-api
```
