# QnA Voice App

A minimal proof-of-concept voice QnA application built with FastAPI, PostgreSQL, and WebRTC. Users can answer predefined questions using their voice, with automatic speech-to-text conversion and text-to-speech for questions.

## Features

- 🎤 **Voice Input**: Record answers using your microphone
- 🔊 **Text-to-Speech**: Questions are automatically converted to speech
- 🗣️ **Speech-to-Text**: Answers are converted from speech to text using OpenAI Whisper
- 💾 **Database Storage**: All sessions and answers stored in PostgreSQL
- 🎨 **Modern UI**: Beautiful, responsive web interface
- 📊 **Session Management**: Track progress and view results

## Tech Stack

- **Backend**: Python FastAPI
- **Database**: PostgreSQL (Supabase/Neon)
- **STT**: OpenAI Whisper (local)
- **TTS**: Google Text-to-Speech (gTTS)
- **Frontend**: HTML/JavaScript with WebRTC
- **ORM**: SQLAlchemy with asyncpg

## Prerequisites

- Python 3.8+
- PostgreSQL database (free tier from Supabase or Neon)
- Microphone access in your browser

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Set Up Database

#### Option A: Supabase (Recommended for free tier)

1. Go to [Supabase](https://supabase.com) and create a free account
2. Create a new project
3. Go to Settings → Database
4. Copy the connection string
5. Update your `.env` file with the connection string

#### Option B: Neon

1. Go to [Neon](https://neon.tech) and create a free account
2. Create a new project
3. Copy the connection string
4. Update your `.env` file with the connection string

### 3. Configure Environment Variables

```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your database URL
nano .env
```

Example `.env` content:
```env
DATABASE_URL=postgresql+asyncpg://postgres:your_password@db.your_project.supabase.co:5432/postgres
HOST=0.0.0.0
PORT=8000
AUDIO_DIR=static/audio
```

### 4. Initialize Database

The application will automatically create tables and insert predefined questions on startup. If you want to manually run the schema:

```bash
# Connect to your database and run the schema
psql your_database_url -f database_schema.sql
```

### 5. Run the Application

```bash
# Start the FastAPI server
python app.py
```

Or using uvicorn directly:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Access the Application

Open your browser and go to: `http://localhost:8000/static/index.html`

## Usage

1. **Start Session**: Click "Start Call" to begin a new QnA session
2. **Listen to Questions**: Questions are automatically played as audio
3. **Record Answers**: Click "Start Recording" and speak your answer
4. **Review Results**: View all your transcribed answers at the end

## API Endpoints

- `GET /` - API health check
- `POST /start-session` - Create a new session
- `GET /next-question?index=n&session_id=...` - Get question with TTS audio
- `POST /submit-answer` - Submit audio answer (STT + save to DB)
- `GET /results/{session_id}` - Get all answers for a session
- `GET /questions` - Get all predefined questions

## Database Schema

### Tables

- **sessions**: Track QnA sessions
- **questions**: Predefined questions
- **answers**: User answers with audio paths

### Views

- **qna_results**: Easy querying of complete QnA sessions

## File Structure

```
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── database_schema.sql    # PostgreSQL schema
├── env.example           # Environment variables template
├── README.md             # This file
├── static/
│   ├── index.html        # Frontend web interface
│   └── audio/            # Generated audio files
└── v1.py                 # Original file (can be removed)
```

## Customization

### Adding New Questions

Edit the `QUESTIONS` array in `app.py`:

```python
QUESTIONS = [
    {"id": 1, "question": "What is your name?"},
    {"id": 2, "question": "How satisfied are you with our service, from 1 to 5?"},
    {"id": 3, "question": "Would you recommend us to a friend?"},
    {"id": 4, "question": "What improvements would you suggest?"},  # New question
]
```

### Changing TTS Language

Modify the gTTS call in `app.py`:

```python
tts = gTTS(text=question["question"], lang='es', slow=False)  # Spanish
```

### Using Different Whisper Model

Change the model size in `app.py`:

```python
whisper_model = whisper.load_model("small")  # or "medium", "large"
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify your `DATABASE_URL` in `.env`
   - Ensure your database is accessible from your IP

2. **Whisper Model Download**
   - First run will download the Whisper model (~1GB)
   - Ensure stable internet connection

3. **Microphone Access**
   - Allow microphone access in your browser
   - Use HTTPS in production (required for WebRTC)

4. **Audio Playback Issues**
   - Check browser console for errors
   - Ensure audio files are generated in `static/audio/`

### Performance Tips

- Use `whisper.load_model("tiny")` for faster processing
- Consider using `faster-whisper` for better performance
- Implement audio file cleanup for old sessions

## Production Deployment

For production deployment:

1. Use a proper WSGI server (Gunicorn)
2. Set up reverse proxy (Nginx)
3. Use HTTPS (required for WebRTC)
4. Implement proper error handling
5. Add authentication if needed
6. Set up monitoring and logging

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues and enhancement requests!
