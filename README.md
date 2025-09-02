Minimal voice QnA system with a React (Vite + TS) frontend and a FastAPI backend using MongoDB. Features Silero VAD for accurate voice detection and a robust TTS fallback mechanism.

## Key Features
- 🎤 **Voice Input**: Record answers using your microphone
- 🔊 **Text-to-Speech**: Multiple TTS providers (Azure, ElevenLabs, Piper) with automatic fallback
- 🎙️ **Voice Activity Detection**: Silero VAD for accurate speech detection
- 🗣️ **Speech-to-Text**: Whisper-based speech recognition
- 🤖 **Intelligent Responses**: LLM-powered dynamic question generation and fallback responses
- 🧠 **Conversation Engine**: Smart context management and dynamic conversation flow
- 💾 **Database Storage**: MongoDB for flexible data storage
- 🎨 **Modern UI**: React + Vite + TypeScript
- 📊 **Analytics Dashboard**: Track sessions and performance

## Structure
```
Hackathon 2025/
├─ frontend/             # React + Vite + Tailwind
└─ v1/                   # FastAPI backend
   ├─ app.py             # API routes
   ├─ database.py        # MongoDB models + queries
   ├─ conversation_engine.py  # LLM-powered conversation management
   ├─ tts_router.py      # TTS provider management
   ├─ run.py             # Backend entrypoint
   ├─ static/audio/      # Generated audio files
   └─ setup_mongodb.py   # DB init/check helper
```

## Prerequisites
- Python 3.10+ and Node 18+
- MongoDB running locally (`mongodb://localhost:27017`)
- Minimum 16GB RAM for Gemma 12B (24GB+ recommended)
- CUDA-capable GPU recommended for optimal LLM performance

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
GEMMA_MODEL_PATH=/path/to/gemma-12b-it
GEMMA_QUANTIZATION=4-bit
GEMMA_MAX_TOKENS=8192
GEMMA_TEMPERATURE=0.7
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

## Voice Activity Detection (VAD)
The system uses Silero VAD (Voice Activity Detection) for precise speech detection:
- Real-time voice activity detection with high accuracy
- Automatic speech segment detection and isolation
- Configurable parameters for sensitivity and speech detection thresholds
- Prevents recording of silence or background noise
- Optimized for real-time processing in browser environment

## Text-to-Speech (TTS) System
The TTS system implements a robust fallback mechanism through `tts_router.py`:

1. **Azure Speech Services (Primary)**
   - High-quality, natural-sounding voices
   - Multiple language support
   - Low latency response

2. **ElevenLabs (Secondary)**
   - Fallback if Azure is unavailable
   - High-quality voice synthesis
   - Emotional tone support

3. **Piper (Local Fallback)**
   - Offline operation capability
   - No external API dependencies
   - Fast local processing
   - Uses local model: `en_US-amy-medium`

The system automatically cascades through providers if the primary option fails, ensuring continuous operation.

## Conversation Engine & LLM Integration
The system features an intelligent conversation engine powered by Large Language Models:

### Conversation Engine (`conversation_engine.py`)
- Dynamic conversation flow management
- Context-aware question generation
- Session state tracking and history management
- Adaptive response handling
- Real-time conversation analysis

### LLM Integration (Gemma 12B)
The system leverages Google's Gemma 12B model running locally for advanced conversational AI capabilities:

1. **Dynamic Question Generation**
   - Context-aware question formulation using conversation history
   - Personalized follow-up questions based on previous responses
   - Adaptive difficulty levels with custom instruction tuning
   - Real-time question refinement based on user engagement

2. **Fallback Response Generation**
   - Smart response generation when STT fails or confidence is low
   - Context-preserving answer synthesis using session history
   - Natural conversation continuation with memory of previous interactions
   - Automatic response calibration based on user's speaking style

3. **Conversation Enhancement**
   - Semantic understanding of user responses with local Gemma processing
   - Advanced NLP for context maintenance and topic tracking
   - Real-time conversation adaptation using custom prompts
   - Emotional intelligence and tone matching

4. **Local Model Implementation**
   - Runs Gemma 12B locally for privacy and reduced latency
   - Optimized inference with minimal resource consumption
   - Custom prompt templates for different conversation scenarios
   - No external API dependencies for core LLM functions

Model Configuration:
```python
# Gemma 12B local configuration
model_path = "gemma-12b-it"
quantization = "4-bit"  # Optimized for local running
context_window = 8192   # Extended context for conversation history
temperature = 0.7      # Balanced creativity and consistency
```

The local Gemma implementation ensures:
- Complete privacy of conversation data
- Consistent low-latency responses
- Customizable behavior through instruction tuning
- Seamless integration with VAD and TTS systems

## Notes
- Audio files are saved under `v1/static/audio/` and auto-cleaned periodically.
- Voice segments are automatically trimmed and normalized using VAD
- Whisper is used for STT. If unavailable, a fallback text is stored.
- Audio URLs are served from `/static/audio/...`.
- CORS is enabled for local development. Frontend targets `http://localhost:8000/api`.

## Troubleshooting
- MongoDB: `python setup_mongodb.py test` and `python setup_mongodb.py all`
- 500 on `/api/dashboard`: ensure MongoDB is running; DB returns JSON-safe data now.
- Mic/recording: check browser permissions.
- **TTS issues**: See `v1/TTS_SETUP.md` for detailed troubleshooting.
