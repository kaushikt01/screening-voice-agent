import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from bson import ObjectId

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "qna_voice")

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
sessions_collection = db.sessions
questions_collection = db.questions
answers_collection = db.answers
analytics_collection = db.analytics

# Pydantic models for data validation
class SessionModel(BaseModel):
    id: str = Field(..., description="Unique session identifier")
    client_id: Optional[str] = Field(None, description="Client identifier if available")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="active", description="Session status: active, completed, abandoned")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")

class QuestionModel(BaseModel):
    id: int = Field(..., description="Question identifier")
    question_text: str = Field(..., description="The question text")
    category: str = Field(default="general", description="Question category")
    is_required: bool = Field(default=True, description="Whether this question is required")
    order: int = Field(..., description="Question order in the sequence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional question metadata")

class AnswerModel(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    question_id: int = Field(..., description="Question identifier")
    answer_text: str = Field(..., description="Transcribed answer text")
    answer_audio_path: Optional[str] = Field(None, description="Path to audio file")
    confidence_score: Optional[float] = Field(None, description="Transcription confidence score")
    processing_time_ms: Optional[int] = Field(None, description="Time taken to process the answer")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional answer metadata")

class CallAnalyticsModel(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    question_id: int = Field(..., description="Question identifier")
    response_time_ms: int = Field(..., description="Time taken to respond")
    answer_duration_ms: int = Field(..., description="Duration of the answer")
    audio_quality_score: float = Field(..., description="Audio quality score (0-1)")
    confidence_score: float = Field(..., description="Confidence score (0-1)")
    hesitation_detected: bool = Field(..., description="Whether hesitation was detected")
    completed: bool = Field(..., description="Whether the question was completed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional analytics metadata")

# Database operations
async def init_database():
    """Initialize database with indexes and default questions"""
    try:
        # Create indexes for better performance
        await sessions_collection.create_index("id", unique=True)
        await sessions_collection.create_index("created_at")
        await sessions_collection.create_index("status")
        
        await questions_collection.create_index("id", unique=True)
        await questions_collection.create_index("order")
        await questions_collection.create_index("category")
        
        await answers_collection.create_index("session_id")
        await answers_collection.create_index("question_id")
        await answers_collection.create_index("created_at")
        await answers_collection.create_index([("session_id", 1), ("question_id", 1)], unique=True)
        
        await analytics_collection.create_index("session_id")
        await analytics_collection.create_index("question_id")
        await analytics_collection.create_index("timestamp")
        
        # Insert default questions if they don't exist
        default_questions = [
            {
                "id": 1,
                "question_text": "Let's get started with your name—what's your first and last name?",
                "category": "personal_info",
                "is_required": True,
                "order": 1,
                "metadata": {"type": "name_collection"}
            },
            {
                "id": 2,
                "question_text": "Please share your Social Security Number. If you'd rather skip for now, just say 'skip'.",
                "category": "personal_info",
                "is_required": False,
                "order": 2,
                "metadata": {"type": "ssn_collection", "sensitive": True}
            },
            {
                "id": 3,
                "question_text": "What's your street address, including ZIP code?",
                "category": "personal_info",
                "is_required": True,
                "order": 3,
                "metadata": {"type": "address_collection"}
            },
            {
                "id": 4,
                "question_text": "Are you under the age of 40?",
                "category": "eligibility",
                "is_required": True,
                "order": 4,
                "metadata": {"type": "age_verification"}
            },
            {
                "id": 5,
                "question_text": "Have you or anyone in your household received TANF welfare payments? You can answer 'yes' or 'not applicable'.",
                "category": "eligibility",
                "is_required": True,
                "order": 5,
                "metadata": {"type": "welfare_verification"}
            },
            {
                "id": 6,
                "question_text": "Have you served in the U.S. military?",
                "category": "eligibility",
                "is_required": True,
                "order": 6,
                "metadata": {"type": "military_service"}
            },
            {
                "id": 7,
                "question_text": "In the past year, were you unemployed and did you receive unemployment compensation for at least 27 weeks?",
                "category": "eligibility",
                "is_required": True,
                "order": 7,
                "metadata": {"type": "unemployment_verification"}
            }
        ]
        
        for question in default_questions:
            await questions_collection.update_one(
                {"id": question["id"]},
                {"$setOnInsert": question},
                upsert=True
            )
        
        print(f"[INFO] Database initialized successfully with {len(default_questions)} questions")
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}")
        raise

async def create_session(session_id: str, client_id: Optional[str] = None) -> SessionModel:
    """Create a new session"""
    session_data = SessionModel(
        id=session_id,
        client_id=client_id,
        created_at=datetime.utcnow(),
        status="active"
    )
    
    await sessions_collection.insert_one(session_data.dict())
    return session_data

async def get_session(session_id: str) -> Optional[SessionModel]:
    """Get session by ID"""
    session_data = await sessions_collection.find_one({"id": session_id})
    if session_data:
        return SessionModel(**session_data)
    return None

async def update_session_status(session_id: str, status: str) -> bool:
    """Update session status"""
    result = await sessions_collection.update_one(
        {"id": session_id},
        {"$set": {"status": status}}
    )
    return result.modified_count > 0

async def get_all_questions() -> List[QuestionModel]:
    """Get all questions ordered by sequence"""
    cursor = questions_collection.find().sort("order", 1)
    questions = await cursor.to_list(length=None)
    return [QuestionModel(**q) for q in questions]

async def get_question(question_id: int) -> Optional[QuestionModel]:
    """Get question by ID"""
    question_data = await questions_collection.find_one({"id": question_id})
    if question_data:
        return QuestionModel(**question_data)
    return None

async def save_answer(answer_data: AnswerModel) -> bool:
    """Save an answer to the database"""
    try:
        # Use upsert to prevent duplicate answers for the same session/question
        result = await answers_collection.update_one(
            {"session_id": answer_data.session_id, "question_id": answer_data.question_id},
            {"$set": answer_data.dict()},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save answer: {e}")
        return False

async def get_session_answers(session_id: str) -> List[AnswerModel]:
    """Get all answers for a session"""
    cursor = answers_collection.find({"session_id": session_id}).sort("question_id", 1)
    answers = await cursor.to_list(length=None)
    return [AnswerModel(**a) for a in answers]

async def save_analytics(analytics_data: CallAnalyticsModel) -> bool:
    """Save call analytics"""
    try:
        await analytics_collection.insert_one(analytics_data.dict())
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save analytics: {e}")
        return False

async def get_session_analytics(session_id: str) -> List[CallAnalyticsModel]:
    """Get analytics for a session"""
    cursor = analytics_collection.find({"session_id": session_id}).sort("timestamp", 1)
    analytics = await cursor.to_list(length=None)
    return [CallAnalyticsModel(**a) for a in analytics]

async def get_dashboard_stats() -> Dict[str, Any]:
    """Get dashboard statistics (JSON-serializable)"""
    try:
        # Totals
        total_sessions = await sessions_collection.count_documents({})
        total_answers = await answers_collection.count_documents({})

        # Recent sessions with answer counts (no ObjectId in response)
        sessions_pipeline = [
            {"$sort": {"created_at": -1}},
            {"$limit": 10},
            {
                "$lookup": {
                    "from": "answers",
                    "localField": "id",
                    "foreignField": "session_id",
                    "as": "answers"
                }
            },
            {"$addFields": {"answer_count": {"$size": "$answers"}}},
            {"$project": {"_id": 0, "session_id": "$id", "created_at": 1, "answer_count": 1}}
        ]
        recent_sessions_docs = await sessions_collection.aggregate(sessions_pipeline).to_list(length=None)
        recent_sessions = [
            {
                "session_id": doc.get("session_id"),
                "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
                "answer_count": int(doc.get("answer_count", 0))
            }
            for doc in recent_sessions_docs
        ]

        # Question statistics (no ObjectId in response)
        question_stats_pipeline = [
            {
                "$lookup": {
                    "from": "questions",
                    "localField": "question_id",
                    "foreignField": "id",
                    "as": "question"
                }
            },
            {"$unwind": "$question"},
            {
                "$group": {
                    "_id": "$question_id",
                    "question": {"$first": "$question.question_text"},
                    "answer_count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 0, "question": 1, "answer_count": 1}}
        ]
        question_stats_docs = await answers_collection.aggregate(question_stats_pipeline).to_list(length=None)
        question_stats = [
            {"question": d.get("question", ""), "answer_count": int(d.get("answer_count", 0))}
            for d in question_stats_docs
        ]

        # Average answer length
        avg_pipeline = [
            {"$addFields": {"answer_length": {"$strLenCP": "$answer_text"}}},
            {"$group": {"_id": None, "avg_length": {"$avg": "$answer_length"}}},
            {"$project": {"_id": 0, "avg_length": 1}}
        ]
        avg_result = await answers_collection.aggregate(avg_pipeline).to_list(length=None)
        avg_answer_length = avg_result[0]["avg_length"] if avg_result else 0

        return {
            "total_sessions": int(total_sessions),
            "total_answers": int(total_answers),
            "recent_sessions": recent_sessions,
            "question_stats": question_stats,
            "avg_answer_length": round(float(avg_answer_length), 1)
        }

    except Exception as e:
        print(f"[ERROR] Failed to get dashboard stats: {e}")
        return {
            "total_sessions": 0,
            "total_answers": 0,
            "recent_sessions": [],
            "question_stats": [],
            "avg_answer_length": 0
        }

# Health check
async def check_database_health() -> bool:
    """Check if database is accessible"""
    try:
        await db.command("ping")
        return True
    except Exception as e:
        print(f"[ERROR] Database health check failed: {e}")
        return False
