#!/usr/bin/env python3
"""
MongoDB Setup Script for QnA Voice Application

This script helps set up MongoDB for the QnA Voice application.
It can be used to:
1. Test MongoDB connection
2. Initialize the database with default questions
3. Check database health
4. View existing data
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from database import init_database, check_database_health, get_all_questions, get_session_answers

# MongoDB connection settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "qna_voice")

async def test_connection():
    """Test MongoDB connection"""
    print("🔍 Testing MongoDB connection...")
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        # Test connection
        await db.command("ping")
        print("✅ MongoDB connection successful!")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

async def initialize_database():
    """Initialize database with default questions"""
    print("🔧 Initializing database...")
    try:
        await init_database()
        print("✅ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

async def check_health():
    """Check database health"""
    print("🏥 Checking database health...")
    try:
        healthy = await check_database_health()
        if healthy:
            print("✅ Database is healthy!")
        else:
            print("❌ Database health check failed!")
        return healthy
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def view_questions():
    """View all questions in the database"""
    print("📋 Viewing questions in database...")
    try:
        questions = await get_all_questions()
        if questions:
            print(f"✅ Found {len(questions)} questions:")
            for q in questions:
                print(f"  {q.id}. {q.question_text} (Category: {q.category})")
        else:
            print("❌ No questions found in database")
        return True
    except Exception as e:
        print(f"❌ Failed to view questions: {e}")
        return False

async def view_sessions():
    """View recent sessions"""
    print("📊 Viewing recent sessions...")
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        sessions = await db.sessions.find().sort("created_at", -1).limit(5).to_list(length=None)
        if sessions:
            print(f"✅ Found {len(sessions)} recent sessions:")
            for s in sessions:
                print(f"  Session: {s['id']} - Created: {s['created_at']} - Status: {s['status']}")
        else:
            print("❌ No sessions found in database")
        return True
    except Exception as e:
        print(f"❌ Failed to view sessions: {e}")
        return False

async def view_answers(session_id=None):
    """View answers for a session or all answers"""
    print("💬 Viewing answers...")
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        if session_id:
            answers = await db.answers.find({"session_id": session_id}).sort("question_id", 1).to_list(length=None)
            print(f"✅ Found {len(answers)} answers for session {session_id}:")
        else:
            answers = await db.answers.find().sort("created_at", -1).limit(10).to_list(length=None)
            print(f"✅ Found {len(answers)} recent answers:")
        
        for a in answers:
            print(f"  Q{a['question_id']}: {a['answer_text'][:50]}... (Session: {a['session_id']})")
        
        return True
    except Exception as e:
        print(f"❌ Failed to view answers: {e}")
        return False

async def main():
    """Main function"""
    print("🚀 QnA Voice MongoDB Setup Script")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage: python setup_mongodb.py <command>")
        print("Commands:")
        print("  test     - Test MongoDB connection")
        print("  init     - Initialize database with default questions")
        print("  health   - Check database health")
        print("  questions - View all questions")
        print("  sessions - View recent sessions")
        print("  answers  - View recent answers")
        print("  all      - Run all checks")
        return
    
    command = sys.argv[1].lower()
    
    if command == "test":
        await test_connection()
    elif command == "init":
        if await test_connection():
            await initialize_database()
    elif command == "health":
        await check_health()
    elif command == "questions":
        await view_questions()
    elif command == "sessions":
        await view_sessions()
    elif command == "answers":
        session_id = sys.argv[2] if len(sys.argv) > 2 else None
        await view_answers(session_id)
    elif command == "all":
        print("Running all checks...")
        await test_connection()
        await check_health()
        await view_questions()
        await view_sessions()
        await view_answers()
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    asyncio.run(main())
