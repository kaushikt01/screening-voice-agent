import os
import uuid
import asyncio
import whisper
import tempfile
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, text
from sqlalchemy.sql import func
from gtts import gTTS
import aiofiles

# Create FastAPI app
app = FastAPI(title="QnA Voice App", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Database setup - Using SQLite for better compatibility
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./qna_voice.db")
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Create static files directory for audio files
AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database Models
class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    status = Column(String, default="active")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True)
    question_text = Column(Text, nullable=False)

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    answer_audio_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

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

# Predefined questions
QUESTIONS = [
    {"id": 1, "question": "What is your name?"},
    {"id": 2, "question": "How satisfied are you with our service, from 1 to 5?"},
    {"id": 3, "question": "Would you recommend us to a friend?"}
]

# Initialize Whisper model
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = whisper.load_model("base")
    return whisper_model

# Database dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database with questions
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        # Check if questions already exist
        result = await session.execute(text("SELECT COUNT(*) FROM questions"))
        count = result.scalar()
        
        if count == 0:
            # Insert predefined questions
            for question in QUESTIONS:
                db_question = Question(id=question["id"], question_text=question["question"])
                session.add(db_question)
            await session.commit()

@app.on_event("startup")
async def startup_event():
    await init_db()

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/index.html", response_class=HTMLResponse)
async def serve_index():
    """Serve the main HTML page"""
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/next-question")
async def get_next_question(index: int, session_id: str):
    """Get the next question and generate TTS audio"""
    if index >= len(QUESTIONS):
        raise HTTPException(status_code=404, detail="No more questions")
    
    question = QUESTIONS[index]
    
    # Generate TTS audio
    tts = gTTS(text=question["question"], lang='en', slow=False)
    audio_filename = f"question_{question['id']}_{session_id}.mp3"
    audio_path = AUDIO_DIR / audio_filename
    
    # Save audio file
    tts.save(str(audio_path))
    
    return QuestionResponse(
        id=question["id"],
        question_text=question["question"],
        audio_url=f"/static/audio/{audio_filename}"
    )

@app.post("/submit-answer")
async def submit_answer(
    session_id: str = Form(...),
    question_id: int = Form(...),
    audio_file: UploadFile = File(...)
):
    """Submit audio answer, convert to text, and save to database"""
    
    # Save uploaded audio file
    audio_filename = f"answer_{question_id}_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    audio_path = AUDIO_DIR / audio_filename
    
    # Read and save audio file
    audio_content = await audio_file.read()
    async with aiofiles.open(audio_path, 'wb') as f:
        await f.write(audio_content)
    
    # Convert audio to text using Whisper
    model = get_whisper_model()
    
    # Use temporary file for Whisper processing
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_file.write(audio_content)
        temp_file_path = temp_file.name
    
    try:
        result = model.transcribe(temp_file_path)
        answer_text = result["text"].strip()
    finally:
        os.unlink(temp_file_path)
    
    # Save to database
    async with AsyncSessionLocal() as session:
        answer = Answer(
            session_id=session_id,
            question_id=question_id,
            answer_text=answer_text,
            answer_audio_path=str(audio_path)
        )
        
        session.add(answer)
        await session.commit()
        await session.refresh(answer)
    
    return {
        "success": True,
        "answer_text": answer_text,
        "question_id": question_id
    }

@app.get("/results/{session_id}")
async def get_results(session_id: str):
    """Get all answers for a session"""
    
    async with AsyncSessionLocal() as session:
        # Get session
        session_result = await session.execute(
            text("SELECT * FROM sessions WHERE id = :session_id"),
            {"session_id": session_id}
        )
        session_data = session_result.fetchone()
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get all answers for the session
        answers_result = await session.execute(text("""
            SELECT a.id, a.question_id, a.answer_text, a.created_at, q.question_text
            FROM answers a
            JOIN questions q ON a.question_id = q.id
            WHERE a.session_id = :session_id
            ORDER BY a.question_id
        """), {"session_id": session_id})
        
        answers = []
        for row in answers_result.fetchall():
            answers.append({
                "id": row[0],
                "question_id": row[1],
                "question_text": row[4],
                "answer_text": row[2],
                "created_at": row[3].isoformat() if row[3] else None
            })
        
        return SessionResult(session_id=session_id, answers=answers)

@app.post("/start-session")
async def start_session():
    """Start a new session"""
    session_id = str(uuid.uuid4())
    
    async with AsyncSessionLocal() as session:
        session_obj = Session(id=session_id, status="active")
        session.add(session_obj)
        await session.commit()
    
    return {"session_id": session_id, "total_questions": len(QUESTIONS)}

@app.get("/questions")
async def get_all_questions():
    """Get all questions"""
    return {"questions": QUESTIONS}

@app.get("/dashboard")
async def get_dashboard_data():
    """Get dashboard analytics data"""
    async with AsyncSessionLocal() as session:
        # Get total sessions
        sessions_result = await session.execute(text("SELECT COUNT(*) FROM sessions"))
        total_sessions = sessions_result.scalar()
        
        # Get total answers
        answers_result = await session.execute(text("SELECT COUNT(*) FROM answers"))
        total_answers = answers_result.scalar()
        
        # Get recent sessions (last 10)
        recent_sessions_result = await session.execute(text("""
            SELECT s.id, s.created_at, COUNT(a.id) as answer_count
            FROM sessions s
            LEFT JOIN answers a ON s.id = a.session_id
            GROUP BY s.id, s.created_at
            ORDER BY s.created_at DESC
            LIMIT 10
        """))
        recent_sessions = []
        for row in recent_sessions_result.fetchall():
            recent_sessions.append({
                "session_id": row[0],
                "created_at": row[1].isoformat() if row[1] else None,
                "answer_count": row[2]
            })
        
        # Get question statistics
        question_stats_result = await session.execute(text("""
            SELECT q.question_text, COUNT(a.id) as answer_count
            FROM questions q
            LEFT JOIN answers a ON q.id = a.question_id
            GROUP BY q.id, q.question_text
            ORDER BY q.id
        """))
        question_stats = []
        for row in question_stats_result.fetchall():
            question_stats.append({
                "question": row[0],
                "answer_count": row[1]
            })
        
        # Get average answer length
        avg_length_result = await session.execute(text("""
            SELECT AVG(LENGTH(answer_text)) as avg_length
            FROM answers
        """))
        avg_answer_length = avg_length_result.scalar() or 0
        
        return {
            "total_sessions": total_sessions,
            "total_answers": total_answers,
            "recent_sessions": recent_sessions,
            "question_stats": question_stats,
            "avg_answer_length": round(avg_answer_length, 1)
        }

@app.get("/session/{session_id}/analytics")
async def get_session_analytics(session_id: str):
    """Get detailed analytics for a specific session"""
    async with AsyncSessionLocal() as session:
        # Get session details
        session_result = await session.execute(
            text("SELECT * FROM sessions WHERE id = :session_id"),
            {"session_id": session_id}
        )
        session_data = session_result.fetchone()
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get all answers for the session
        answers_result = await session.execute(text("""
            SELECT a.id, a.question_id, a.answer_text, a.created_at, q.question_text
            FROM answers a
            JOIN questions q ON a.question_id = q.id
            WHERE a.session_id = :session_id
            ORDER BY a.question_id
        """), {"session_id": session_id})
        
        answers = []
        total_words = 0
        for row in answers_result.fetchall():
            answer_text = row[2]
            word_count = len(answer_text.split())
            total_words += word_count
            
            answers.append({
                "id": row[0],
                "question_id": row[1],
                "question_text": row[4],
                "answer_text": answer_text,
                "word_count": word_count,
                "created_at": row[3].isoformat() if row[3] else None
            })
        
        # Calculate analytics
        avg_words_per_answer = round(total_words / len(answers), 1) if answers else 0
        session_duration = None
        if len(answers) >= 2:
            first_answer = answers[0]["created_at"]
            last_answer = answers[-1]["created_at"]
            if first_answer and last_answer:
                from datetime import datetime
                start_time = datetime.fromisoformat(first_answer.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(last_answer.replace('Z', '+00:00'))
                session_duration = (end_time - start_time).total_seconds()
        
        return {
            "session_id": session_id,
            "created_at": session_data[1].isoformat() if session_data[1] else None,
            "total_answers": len(answers),
            "total_words": total_words,
            "avg_words_per_answer": avg_words_per_answer,
            "session_duration_seconds": session_duration,
            "answers": answers
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
