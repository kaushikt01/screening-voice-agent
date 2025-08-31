# QnA Voice Call Bot

Minimal voice QnA system with a React (Vite + TS) frontend and a FastAPI backend using MongoDB.

## Structure
```
Hackathon 2025/
├─ frontend/             # React + Vite + Tailwind
└─ v1/                   # FastAPI backend
   ├─ app.py             # API routes
   ├─ database.py        # MongoDB models + queries
   ├─ run.py             # Backend entrypoint
   ├─ static/audio/      # Generated audio files
   └─ setup_mongodb.py   # DB init/check helper
```

## Prerequisites
- Python 3.10+ and Node 18+
- MongoDB running locally (`mongodb://localhost:27017`)

## Backend (FastAPI)
```bash
cd v1
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Setup TTS (required for voice generation)
pip install piper-tts torch torchaudio
mkdir -p piper_models
# Download voice model:
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx -O piper_models/en_US-amy-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json -O piper_models/en_US-amy-medium.onnx.json

# Initialize DB (first time)
python setup_mongodb.py init
# Run API
python run.py
# API: http://localhost:8000
```

**TTS Troubleshooting:** If you get `ModuleNotFoundError: No module named 'piper'`, see `v1/TTS_SETUP.md` for detailed instructions.

Env (optional):
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=qna_voice
```

## Frontend (Vite + React + TS)
```bash
cd frontend
npm install
npm run dev
# App: http://localhost:5173
```

## Core Endpoints
- GET `/api/health` – service + dependency status
- POST `/api/start-session` – create session
- GET `/api/questions` – list questions
- GET `/api/next-question?index={i}&session_id={id}` – conversational question + TTS audio
- POST `/api/submit-answer` – multipart audio upload (WAV), auto-transcribe, store
- GET `/api/results/{session_id}` – session answers
- GET `/api/dashboard` – totals, recent sessions, question stats, avg answer length
- GET `/api/session/{session_id}/analytics` – per-session analytics

## Notes
- Audio files are saved under `v1/static/audio/` and auto-cleaned periodically.
- Whisper is used for STT. If unavailable, a fallback text is stored.
- TTS is routed via `tts_router.py` (Piper/others); audio URLs are served from `/static/audio/...`.
- CORS is enabled for local development. Frontend targets `http://localhost:8000/api`.

## Troubleshooting
- MongoDB: `python setup_mongodb.py test` and `python setup_mongodb.py all`
- 500 on `/api/dashboard`: ensure MongoDB is running; DB returns JSON-safe data now.
- Mic/recording: check browser permissions.
- **TTS issues**: See `v1/TTS_SETUP.md` for detailed troubleshooting.
