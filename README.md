# QnA Voice Call Bot

A full-stack application for automated voice call analysis with a React frontend and FastAPI backend.

## Project Structure

```
Hackathon 2025/
├── frontend/CallBot/          # React TypeScript frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API service layer
│   │   └── ...
│   └── ...
├── v1/                        # FastAPI backend
│   ├── app.py                 # Main API server
│   ├── static/audio/          # Audio file storage
│   └── ...
└── static/audio/              # Shared audio files
```

## Features

### Frontend (React + TypeScript)
- **Dashboard**: Real-time analytics and call statistics
- **Call Interface**: Interactive call simulation with voice recording
- **Modern UI**: Beautiful, responsive design with Tailwind CSS
- **Real-time Updates**: Live data from backend API

### Backend (FastAPI + Python)
- **Pure API**: RESTful endpoints for frontend communication
- **Voice Processing**: Whisper AI for speech-to-text conversion
- **Text-to-Speech**: gTTS for question audio generation
- **Database**: SQLite with SQLAlchemy ORM
- **CORS Support**: Configured for frontend integration

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/start-session` | POST | Start new call session |
| `/api/questions` | GET | Get all questions |
| `/api/next-question` | GET | Get next question with audio |
| `/api/submit-answer` | POST | Submit voice answer |
| `/api/results/{session_id}` | GET | Get session results |
| `/api/dashboard` | GET | Get dashboard analytics |
| `/api/session/{session_id}/analytics` | GET | Get session analytics |

## Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd v1
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend server:**
   ```bash
   python app.py
   ```
   
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend/CallBot
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:5173` or `http://localhost:5174`

## Integration Details

### API Service Layer
The frontend uses a centralized API service (`src/services/api.ts`) that handles all backend communication:

- **Type Safety**: Full TypeScript interfaces for all API responses
- **Error Handling**: Comprehensive error handling and loading states
- **CORS Configuration**: Backend configured to accept requests from frontend origins

### Data Flow
1. Frontend initializes session via `/api/start-session`
2. Questions are loaded from `/api/questions`
3. Audio files are generated for each question
4. User responses are submitted via `/api/submit-answer`
5. Dashboard displays real-time analytics from `/api/dashboard`

### CORS Configuration
The backend is configured to accept requests from:
- `http://localhost:5173`
- `http://localhost:5174` 
- `http://192.168.1.66:5174`

## Key Features

### Voice Processing
- **Speech-to-Text**: Uses OpenAI Whisper for accurate transcription
- **Text-to-Speech**: gTTS for natural-sounding question audio
- **Audio Storage**: All audio files stored in `static/audio/`

### Database Schema
- **Sessions**: Track call sessions with unique IDs
- **Questions**: Predefined question bank
- **Answers**: Store transcribed responses with audio paths

### Analytics
- **Real-time Dashboard**: Live statistics and metrics
- **Session Analytics**: Detailed call analysis
- **Response Quality**: Track answer completeness and quality

## Development Notes

### Backend Changes Made
- Removed HTML serving endpoints (`/`, `/index.html`)
- Added `/api` prefix to all endpoints
- Updated CORS configuration for frontend integration
- Added health check endpoint
- Updated questions to match frontend requirements

### Frontend Changes Made
- Created API service layer with TypeScript interfaces
- Integrated real API calls in Dashboard and CallInterface
- Added loading states and error handling
- Updated to use real session management

### Audio File Management
- Backend generates audio files for questions
- Frontend can access audio via `/static/audio/` endpoint
- Audio files are named with session IDs for tracking

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure backend CORS configuration includes your frontend URL
2. **Audio Loading**: Check that audio files are being generated in `static/audio/`
3. **Database Issues**: Ensure SQLite database has proper permissions
4. **Port Conflicts**: Frontend may use 5173 or 5174, backend uses 8000

### Ad Blocker Issues
If you see errors related to "fingerprint" icons, this is likely due to ad blockers. Solutions:
- Whitelist `localhost:5173` in your ad blocker
- Use alternative icons (Shield, Lock, etc.) instead of Fingerprint

## Future Enhancements

- Real-time WebSocket communication
- Advanced voice recognition
- Call recording and playback
- User authentication and sessions
- Advanced analytics and reporting
- Mobile app integration
