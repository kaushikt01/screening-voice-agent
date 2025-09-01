import os
import uuid
import asyncio
import whisper
import tempfile
import spacy
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
import glob

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tts_utils import get_gemma_response
from tts_router import generate_tts, generate_conversational_voice, generate_emotional_voice
from conversation_engine import ConversationEngine
from answer_validator import AnswerValidator
from silero_vad import get_vad_instance
from database import (
    init_database, create_session, get_session, update_session_status,
    get_all_questions, get_question, save_answer, get_session_answers,
    save_analytics, get_session_analytics, get_dashboard_stats, check_database_health,
    AnswerModel, CallAnalyticsModel, sessions_collection
)
import aiofiles

# Create FastAPI app
app = FastAPI(title="QnA Voice API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static files directory for audio files
AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files for audio access
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize conversation engine and answer validator
conversation_engine = ConversationEngine()
answer_validator = AnswerValidator()

def cleanup_old_audio_files():
    """Clean up old audio files to prevent directory clutter."""
    try:
        # Remove files older than 1 hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        # Get all audio files
        audio_files = glob.glob(str(AUDIO_DIR / "*.mp3")) + glob.glob(str(AUDIO_DIR / "*.wav"))
        
        for audio_file in audio_files:
            file_path = Path(audio_file)
            if file_path.exists():
                # Get file modification time
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        print(f"Cleaned up old audio file: {file_path.name}")
                    except Exception as e:
                        print(f"Failed to remove old audio file {file_path.name}: {e}")
                        
    except Exception as e:
        print(f"Error during audio cleanup: {e}")

# Pydantic models for API responses


# Pydantic models
class QuestionResponse(BaseModel):
    id: int
    question_text: str
    audio_url: str


class AnswerSubmission(BaseModel):
    session_id: str
    question_id: int


class SessionResult(BaseModel):
    session_id: str
    answers: List[dict]


class CallAnalytics(BaseModel):
    question_id: int
    response_time: int
    answer_duration: int
    audio_quality: float
    confidence: float
    hesitation: bool
    completed: bool
    timestamp: str


class CallAnalyticsSubmission(BaseModel):
    session_id: str
    analytics: List[CallAnalytics]


# Initialize Whisper model
whisper_model = None
whisper_available = True


def get_whisper_model():
    global whisper_model, whisper_available
    
    if not whisper_available:
        print("[WARNING] Whisper is not available, returning None")
        return None
        
    try:
        if whisper_model is None:
            print("[DEBUG] Loading Whisper model...")
            print("[DEBUG] Checking if whisper module is available...")
            print(f"[DEBUG] Whisper module: {whisper}")
            print(f"[DEBUG] Whisper version: {whisper.__version__ if hasattr(whisper, '__version__') else 'Unknown'}")
            
            whisper_model = whisper.load_model("base")
            print("[DEBUG] Whisper model loaded successfully")
            print(f"[DEBUG] Model type: {type(whisper_model)}")
        return whisper_model
    except Exception as e:
        print(f"[ERROR] Failed to load Whisper model: {e}")
        print(f"[ERROR] Error type: {type(e)}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        whisper_available = False
        return None


def transcribe_audio_fallback(audio_path: str) -> str:
    """Fallback transcription when Whisper is not available."""
    print("[DEBUG] Using fallback transcription")
    # Return a more descriptive placeholder text
    return "audio recorded successfully - transcription pending"


# Load spaCy model once
nlp = None
spacy_available = True

try:
    nlp = spacy.load("en_core_web_sm")
    print("[DEBUG] spaCy model loaded successfully")
except Exception as e:
    print(f"[ERROR] Failed to load spaCy model: {e}")
    spacy_available = False


def extract_name(text: str) -> Optional[str]:
    """Extract name using spaCy NER"""
    if not spacy_available or nlp is None:
        print("[WARNING] spaCy not available, returning original text")
        return text.strip()
        
    try:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text.strip()
        return text.strip()  # fallback: just return original if no PERSON found
    except Exception as e:
        print(f"[ERROR] Name extraction failed: {e}")
        return text.strip()


# Initialize database
async def init_db():
    await init_database()


@app.on_event("startup")
async def startup_event():
    await init_db()
    
    # Test Whisper availability on startup
    print("[DEBUG] Testing Whisper availability on startup...")
    try:
        test_model = get_whisper_model()
        if test_model:
            print("[DEBUG] ✅ Whisper is available and working")
        else:
            print("[DEBUG] ❌ Whisper is not available")
    except Exception as e:
        print(f"[ERROR] Whisper startup test failed: {e}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")


# API Endpoints
@app.get("/api/health")
async def health_check():
    # Check database health
    db_healthy = await check_database_health()
    
    # Check Whisper status
    whisper_status = "unknown"
    try:
        if whisper_available:
            if whisper_model:
                whisper_status = "loaded"
            else:
                whisper_status = "available"
        else:
            whisper_status = "unavailable"
    except:
        whisper_status = "error"
    
    return {
        "status": "healthy" if db_healthy else "unhealthy", 
        "message": "QnA Voice API is running",
        "database_status": "connected" if db_healthy else "disconnected",
        "whisper_status": whisper_status,
        "spacy_status": "available" if spacy_available else "unavailable"
    }

@app.post("/api/cleanup-audio")
async def cleanup_audio():
    """Clean up old audio files manually."""
    try:
        cleanup_old_audio_files()
        return {"status": "success", "message": "Audio cleanup completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@app.get("/api/introduction")
async def get_introduction_audio():
    """Generate introduction audio for the call using Gemma and TTS utils"""
    intro_prompt = (
        "You are an HR assistant calling an employee (use any random name everytime) on behalf of their organization(ADP) to collect brief WOTC eligibility information. You are Sarah"
        "Write a single, concise, natural spoken greeting from the caller (no options, no lists). "
        "Max 2 short sentences, under 12 seconds. "
        "Make it friendly, professional, and immediately set context that a few short questions will follow."
    )
    intro_text = get_gemma_response(intro_prompt)
    audio_filename = "introduction.mp3"
    audio_url = generate_tts(intro_text, audio_filename)
    return {"audio_url": audio_url, "text": intro_text}


@app.get("/api/next-question")
async def get_next_question_endpoint(index: int, session_id: str):
    """Get next question with dynamic, conversational text."""
    print(f"[DEBUG] /api/next-question called with index={index}, session_id={session_id}")
    
    try:
        # Get all questions from database
        questions = await get_all_questions()
        
        if index >= len(questions):
            print(f"[ERROR] Index {index} out of range. Total questions: {len(questions)}")
            raise HTTPException(status_code=404, detail="No more questions")

        question = questions[index]
        
        # Map question index to conversation topic safely
        topic_mapping = {
            0: "name",
            1: "ssn",
            2: "address",
            3: "cash_assistance",
            4: "eligibility_limitation",
            5: "other_assistance",
            6: "felony",
            7: "vocational_rehab",
            8: "ssi",
            9: "manager_info",
            10: "eligibility_result",
            11: "hire_date",
            12: "start_date",
            13: "confirmation"
        }
        
        topic_key = topic_mapping.get(index, "general")
        
        try:
            # Use conversation engine to make questions more natural
            if topic_key in conversation_engine.conversation_topics:
                conversational_text = conversation_engine._get_natural_question(topic_key)
            else:
                # Fallback to original question text if topic not found
                conversational_text = question.question_text
                
        except Exception as e:
            print(f"[WARNING] Conversation engine failed for topic {topic_key}: {e}")
            # Fallback to original question text
            conversational_text = question.question_text
        
        print(f"[DEBUG] Generated conversational text: {conversational_text}")
        audio_filename = f"question_{question.id}_{session_id}.mp3"
        audio_url = generate_conversational_voice(conversational_text, audio_filename, "friendly")
        if not audio_url or not os.path.exists(f"static/audio/{audio_filename}"):
            print(f"[ERROR] TTS failed to generate audio for: {audio_filename}")

        return QuestionResponse(
            id=question.id,
            question_text=conversational_text,
            audio_url=audio_url
        )
    except Exception as e:
        print(f"[ERROR] Failed to get next question: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get next question: {str(e)}")


@app.post("/api/submit-answer")
async def submit_answer(
        session_id: str = Form(...),
        question_id: int = Form(...),
        audio_file: UploadFile = File(...)
):
    """Submit an answer to a question."""
    try:
        print(f"[DEBUG] submit_answer called with session_id: {session_id}, question_id: {question_id}")
        
        audio_filename = f"answer_{question_id}_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        audio_path = AUDIO_DIR / audio_filename

        print(f"[DEBUG] Saving audio to: {audio_path}")
        audio_content = await audio_file.read()
        async with aiofiles.open(audio_path, 'wb') as f:
            await f.write(audio_content)

        print(f"[DEBUG] Audio saved, size: {len(audio_content)} bytes")

        print(f"[DEBUG] Loading Whisper model...")
        model = get_whisper_model()
        
        if model is None:
            print("[DEBUG] Whisper model not available, using fallback")
            answer_text = transcribe_audio_fallback(str(audio_path))
        else:
            print(f"[DEBUG] Whisper model loaded successfully")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_content)
                temp_file_path = temp_file.name

            try:
                print(f"[DEBUG] Starting Whisper transcription...")
                result = model.transcribe(temp_file_path)
                answer_text = result["text"].strip()
                print(f"[DEBUG] Whisper transcription result: '{answer_text}'")
                print(f"[DEBUG] Transcription result type: {type(result)}")
                print(f"[DEBUG] Full result: {result}")
                
                # Validate transcription result
                if not answer_text or answer_text.strip() == "":
                    print("[WARNING] Whisper returned empty text, using fallback")
                    answer_text = transcribe_audio_fallback(str(audio_path))
                    
            except Exception as e:
                print(f"[ERROR] Whisper transcription failed: {e}")
                print(f"[DEBUG] Using fallback transcription due to Whisper error")
                answer_text = transcribe_audio_fallback(str(audio_path))
            finally:
                os.unlink(temp_file_path)

        # 🔹 If Q1, extract only name with spaCy
        if question_id == 1:
            try:
                extracted_text = extract_name(answer_text)
                print(f"[DEBUG] Q1 name extraction: '{answer_text}' -> '{extracted_text}'")
            except Exception as e:
                print(f"[ERROR] Name extraction failed: {e}")
                extracted_text = answer_text
        else:
            extracted_text = answer_text
            print(f"[DEBUG] Non-Q1 answer: '{extracted_text}'")

        print(f"[DEBUG] Final answer_text to save: '{extracted_text}'")
        print(f"[DEBUG] Audio path to save: '{audio_path}'")

        # Validate that we have some text content
        if not extracted_text or extracted_text.strip() == "":
            print("[WARNING] Empty answer text detected, using fallback text")
            extracted_text = "audio recorded successfully - transcription pending"

        print(f"[DEBUG] Final validated answer_text: '{extracted_text}'")
        
        # 🔹 Validate answer using local LLM
        print(f"[DEBUG] Starting answer validation for question {question_id}...")
        try:
            # Get the question text for validation
            question = await get_question(question_id)
            question_text = question.question_text if question else f"Question {question_id}"
            
            # Validate the answer
            is_valid, fallback_message = await answer_validator.validate_answer(
                question_id, question_text, extracted_text
            )
            
            print(f"[DEBUG] Answer validation result: valid={is_valid}, fallback='{fallback_message}'")
            
            if not is_valid:
                print(f"[DEBUG] Answer validation failed, returning fallback response")
                print(f"[DEBUG] Question: {question_text}")
                print(f"[DEBUG] Answer: {extracted_text}")
                print(f"[DEBUG] Fallback: {fallback_message}")
                return {
                    "success": False,
                    "validation_failed": True,
                    "fallback_message": fallback_message,
                    "question_id": question_id,
                    "original_answer": extracted_text
                }
            
        except Exception as e:
            print(f"[ERROR] Answer validation failed: {e}")
            # If validation fails, continue with the answer as-is
            print(f"[DEBUG] Continuing with answer despite validation error")
        
        print(f"[DEBUG] Answer validation passed, saving to database...")
        try:
            # Create answer model
            answer_data = AnswerModel(
                session_id=session_id,
                question_id=question_id,
                answer_text=extracted_text,
                answer_audio_path=str(audio_path),
                processing_time_ms=int((datetime.now() - datetime.now()).total_seconds() * 1000)  # Placeholder
            )
            
            # Save to database
            success = await save_answer(answer_data)
            
            if success:
                print(f"[DEBUG] Answer saved to database successfully")
                print(f"[DEBUG] Saved answer_text: '{answer_data.answer_text}'")
                print(f"[DEBUG] Saved audio_path: '{answer_data.answer_audio_path}'")
                
                return {
                    "success": True,
                    "answer_text": extracted_text,
                    "question_id": question_id
                }
            else:
                print(f"[ERROR] Failed to save answer to database")
                return {
                    "success": True,
                    "answer_text": extracted_text,
                    "question_id": question_id,
                    "warning": "Answer saved to audio file but not to database"
                }
        except Exception as e:
            print(f"[ERROR] Database operation failed: {e}")
            # Even if database fails, return success to continue the flow
            # The audio file is still saved, so we can retry later
            return {
                "success": True,
                "answer_text": extracted_text,
                "question_id": question_id,
                "warning": "Answer saved to audio file but not to database"
            }
        
    except Exception as e:
        print(f"[ERROR] submit_answer failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/results/{session_id}")
async def get_results_endpoint(session_id: str):
    try:
        # Check if session exists
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get answers for the session
        answers = await get_session_answers(session_id)
        
        # Get questions for reference
        questions = await get_all_questions()
        questions_dict = {q.id: q.question_text for q in questions}
        
        # Format response
        formatted_answers = []
        for answer in answers:
            formatted_answers.append({
                "id": str(answer.created_at.timestamp()),  # Use timestamp as ID
                "question_id": answer.question_id,
                "question_text": questions_dict.get(answer.question_id, "Unknown question"),
                "answer_text": answer.answer_text,
                "created_at": answer.created_at.isoformat() if answer.created_at else None
            })

        return SessionResult(session_id=session_id, answers=formatted_answers)
    except Exception as e:
        print(f"[ERROR] Failed to get results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@app.post("/api/start-session")
async def start_session():
    # Clean up old audio files before starting new session
    cleanup_old_audio_files()
    
    session_id = str(uuid.uuid4())
    try:
        await create_session(session_id)
        questions = await get_all_questions()
        return {"session_id": session_id, "total_questions": len(questions)}
    except Exception as e:
        print(f"[ERROR] Failed to start session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@app.get("/api/questions")
async def get_questions_endpoint():
    try:
        questions = await get_all_questions()
        return {"questions": [{"id": q.id, "question": q.question_text} for q in questions]}
    except Exception as e:
        print(f"[ERROR] Failed to get questions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get questions: {str(e)}")


@app.get("/api/dashboard")
async def get_dashboard_data_endpoint():
    try:
        return await get_dashboard_stats()
    except Exception as e:
        print(f"[ERROR] Failed to get dashboard data: {e}")
        # Return default data if there's any error
        return {
            "total_sessions": 0,
            "total_answers": 0,
            "recent_sessions": [],
            "question_stats": [],
            "avg_answer_length": 0
        }


@app.post("/api/save-call-analytics")
async def save_call_analytics(analytics_data: CallAnalyticsSubmission):
    try:
        print(f"Call Analytics for session {analytics_data.session_id}:")
        
        # Save each analytics entry to database
        for analytics in analytics_data.analytics:
            analytics_model = CallAnalyticsModel(
                session_id=analytics_data.session_id,
                question_id=analytics.question_id,
                response_time_ms=analytics.response_time,
                answer_duration_ms=analytics.answer_duration,
                audio_quality_score=analytics.audio_quality,
                confidence_score=analytics.confidence,
                hesitation_detected=analytics.hesitation,
                completed=analytics.completed,
                timestamp=datetime.fromisoformat(analytics.timestamp.replace('Z', '+00:00'))
            )
            
            success = await save_analytics(analytics_model)
            if success:
                print(f"  Question {analytics.question_id}: Response time={analytics.response_time}ms, "
                      f"Duration={analytics.answer_duration}ms, Quality={analytics.audio_quality}, "
                      f"Hesitation={analytics.hesitation} - SAVED")
            else:
                print(f"  Question {analytics.question_id}: FAILED TO SAVE")
        
        return {"success": True, "message": "Analytics saved successfully"}
    except Exception as e:
        print(f"[ERROR] Failed to save analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save analytics: {str(e)}")


@app.get("/api/sessions/search")
async def search_sessions(
    query: str = "",
    limit: int = 20,
    offset: int = 0
):
    """Search sessions by session ID or client information"""
    try:
        # Build search query
        search_filter = {}
        if query.strip():
            # Search by session ID (partial match)
            search_filter["id"] = {"$regex": query, "$options": "i"}
        
        # Get sessions with answer counts
        sessions_pipeline = [
            {"$match": search_filter},
            {"$sort": {"created_at": -1}},
            {"$skip": offset},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "answers",
                    "localField": "id",
                    "foreignField": "session_id",
                    "as": "answers"
                }
            },
            {"$addFields": {"answer_count": {"$size": "$answers"}}},
            {
                "$project": {
                    "_id": 0,
                    "session_id": "$id",
                    "created_at": 1,
                    "answer_count": 1,
                    "status": 1,
                    "client_id": 1
                }
            }
        ]
        
        sessions_docs = await sessions_collection.aggregate(sessions_pipeline).to_list(length=None)
        
        # Format sessions
        sessions = []
        for doc in sessions_docs:
            # Get first answer to extract client name if available
            first_answer = None
            if doc.get("answer_count", 0) > 0:
                answers = await get_session_answers(doc["session_id"])
                if answers:
                    first_answer = answers[0].answer_text
            
            sessions.append({
                "session_id": doc.get("session_id"),
                "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
                "answer_count": int(doc.get("answer_count", 0)),
                "status": doc.get("status", "unknown"),
                "client_id": doc.get("client_id"),
                "client_name": first_answer if first_answer else "Unknown Client"
            })
        
        return {
            "sessions": sessions,
            "total": len(sessions),
            "query": query,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        print(f"[ERROR] Failed to search sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search sessions: {str(e)}")


@app.get("/api/session/{session_id}/analytics")
async def get_session_analytics_endpoint(session_id: str):
    try:
        # Check if session exists
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get answers for the session
        answers = await get_session_answers(session_id)
        
        # Get questions for reference
        questions = await get_all_questions()
        questions_dict = {q.id: q.question_text for q in questions}
        
        # Process answers
        formatted_answers = []
        total_words = 0
        for answer in answers:
            answer_text = answer.answer_text
            word_count = len(answer_text.split())
            total_words += word_count
            formatted_answers.append({
                "id": str(answer.created_at.timestamp()),
                "question_id": answer.question_id,
                "question_text": questions_dict.get(answer.question_id, "Unknown question"),
                "answer_text": answer_text,
                "word_count": word_count,
                "created_at": answer.created_at.isoformat() if answer.created_at else None
            })

        avg_words_per_answer = round(total_words / len(formatted_answers), 1) if formatted_answers else 0
        session_duration = None
        if len(formatted_answers) >= 2:
            first_answer = formatted_answers[0]["created_at"]
            last_answer = formatted_answers[-1]["created_at"]
            if first_answer and last_answer:
                start_time = datetime.fromisoformat(first_answer.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(last_answer.replace('Z', '+00:00'))
                session_duration = (end_time - start_time).total_seconds()

        return {
            "session_id": session_id,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "total_answers": len(formatted_answers),
            "total_words": total_words,
            "avg_words_per_answer": avg_words_per_answer,
            "session_duration_seconds": session_duration,
            "answers": formatted_answers
        }
    except Exception as e:
        print(f"[ERROR] Failed to get session analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session analytics: {str(e)}")


@app.get("/api/test-validation")
async def test_validation(
    question_id: int = 1,
    question_text: str = "What's your first and last name?",
    answer_text: str = "Hello there"
):
    """Test endpoint for answer validation."""
    try:
        is_valid, fallback_message = await answer_validator.validate_answer(
            question_id, question_text, answer_text
        )
        
        return {
            "question_id": question_id,
            "question_text": question_text,
            "answer_text": answer_text,
            "is_valid": is_valid,
            "fallback_message": fallback_message
        }
    except Exception as e:
        print(f"[ERROR] Test validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation test failed: {str(e)}")


class FallbackAudioRequest(BaseModel):
    text: str
    style: str = "friendly"

@app.post("/api/generate-fallback-audio")
async def generate_fallback_audio(request: FallbackAudioRequest):
    """Generate audio for fallback messages."""
    try:
        print(f"[DEBUG] Generating fallback audio for: '{request.text}' with style: {request.style}")
        
        # Generate unique filename
        audio_filename = f"fallback_{uuid.uuid4().hex[:8]}.mp3"
        
        # Generate audio using TTS
        audio_url = generate_conversational_voice(request.text, audio_filename, request.style)
        
        if not audio_url:
            print(f"[ERROR] Failed to generate fallback audio for: {request.text}")
            raise HTTPException(status_code=500, detail="Failed to generate audio")
        
        print(f"[DEBUG] Fallback audio generated: {audio_url}")
        return {"audio_url": audio_url}
        
    except Exception as e:
        print(f"[ERROR] Failed to generate fallback audio: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate fallback audio: {str(e)}")


@app.post("/api/vad-detect")
async def vad_detect_silence(audio_chunk: UploadFile = File(...)):
    """Detect silence using Silero VAD"""
    try:
        # Read audio chunk
        audio_data = await audio_chunk.read()
        print(f"[DEBUG] VAD received audio chunk: {len(audio_data)} bytes")
        
        # Validate audio data
        if len(audio_data) == 0:
            print("[WARNING] Empty audio chunk received, treating as silence")
            return {
                "is_silent": True,
                "speech_confidence": 0.0,
                "audio_duration": 0.0
            }
        
        # Get VAD instance
        vad = get_vad_instance()
        
        # Convert audio to numpy array (handling WebM and WAV files)
        import numpy as np
        import wave
        import io
        import subprocess
        import tempfile
        import os
        
        try:
            # Try to parse as WAV file first
            with io.BytesIO(audio_data) as wav_io:
                with wave.open(wav_io, 'rb') as wav_file:
                    # Get WAV parameters
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    sample_rate = wav_file.getframerate()
                    n_frames = wav_file.getnframes()
                    
                    # Read audio data
                    audio_data_raw = wav_file.readframes(n_frames)
                    
                    # Convert to numpy array based on sample width
                    if sample_width == 2:  # 16-bit
                        audio_array = np.frombuffer(audio_data_raw, dtype=np.int16).astype(np.float32) / 32768.0
                    elif sample_width == 1:  # 8-bit
                        audio_array = np.frombuffer(audio_data_raw, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
                    else:
                        audio_array = np.frombuffer(audio_data_raw, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # Convert to mono if stereo
                    if channels == 2:
                        audio_array = audio_array.reshape(-1, 2).mean(axis=1)
                    
                    print(f"[DEBUG] WAV parsed - channels: {channels}, sample_width: {sample_width}, sample_rate: {sample_rate}, frames: {n_frames}")
                    
        except Exception as wav_error:
            print(f"[WARNING] Failed to parse as WAV, trying WebM/MP4: {wav_error}")
            
            except Exception as webm_error:
                print(f"[WARNING] Failed to parse as WAV, treating as silence: {webm_error}")
                # For now, treat any unparseable audio as silence to prevent errors
                # This allows the VAD to continue working while we debug the audio format
                audio_array = np.array([0.0], dtype=np.float32)  # Single sample of silence
        
        print(f"[DEBUG] Audio array shape: {audio_array.shape}, duration: {len(audio_array) / 16000.0:.2f}s")
        
        # Calculate basic audio stats for debugging
        rms = np.sqrt(np.mean(audio_array**2))
        max_amplitude = np.max(np.abs(audio_array))
        print(f"[DEBUG] Audio stats - RMS: {rms:.4f}, Max: {max_amplitude:.4f}")
        
        # Detect silence (1.5 seconds threshold)
        is_silent = vad.is_silence(audio_array, sample_rate=16000, min_silence_duration=1.5)
        
        # Get speech confidence
        confidence = vad.get_speech_confidence(audio_array, sample_rate=16000)
        
        print(f"[DEBUG] VAD Result - Silent: {is_silent}, Confidence: {confidence:.3f}")
        
        return {
            "is_silent": is_silent,
            "speech_confidence": confidence,
            "audio_duration": len(audio_array) / 16000.0
        }
        
    except Exception as e:
        print(f"[ERROR] VAD detection failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"VAD detection failed: {str(e)}")


@app.get("/api/debug/answers/{session_id}")
async def debug_answers(session_id: str):
    """Debug endpoint to check what's stored in the database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT * FROM answers WHERE session_id = :session_id ORDER BY question_id"),
            {"session_id": session_id}
        )
        answers = result.fetchall()
        
        debug_data = []
        for row in answers:
            debug_data.append({
                "id": row[0],
                "session_id": row[1],
                "question_id": row[2],
                "answer_text": row[3],
                "answer_audio_path": row[4],
                "created_at": row[5] if len(row) > 5 else None
            })
        
        return {
            "session_id": session_id,
            "total_answers": len(debug_data),
            "answers": debug_data
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)