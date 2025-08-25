#!/usr/bin/env python3
"""
Database initialization script for QnA Voice App
"""

import asyncio
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, text
from sqlalchemy.sql import func

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./qna_voice.db"
engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()

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

# Predefined questions
QUESTIONS = [
    {"id": 1, "question": "What is your company size?"},
    {"id": 2, "question": "What industry are you in?"},
    {"id": 3, "question": "What is your annual revenue?"},
    {"id": 4, "question": "Do you currently use CRM software?"},
    {"id": 5, "question": "What are your main pain points?"},
    {"id": 6, "question": "What is your budget range?"},
    {"id": 7, "question": "When are you looking to implement?"},
    {"id": 8, "question": "Who makes the purchasing decisions?"},
    {"id": 9, "question": "Have you evaluated other solutions?"},
    {"id": 10, "question": "What features are most important?"}
]

async def init_database():
    """Initialize the database with tables and questions"""
    print("🔄 Initializing database...")
    
    # Remove existing database file if it exists
    db_file = Path("qna_voice.db")
    if db_file.exists():
        db_file.unlink()
        print("🗑️  Removed existing database file")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Created database tables")
    
    # Insert questions
    async with engine.begin() as conn:
        for question in QUESTIONS:
            await conn.execute(
                text("INSERT INTO questions (id, question_text) VALUES (:id, :question_text)"),
                {"id": question["id"], "question_text": question["question"]}
            )
    print(f"✅ Inserted {len(QUESTIONS)} questions")
    
    print("🎉 Database initialization completed!")

if __name__ == "__main__":
    asyncio.run(init_database())
