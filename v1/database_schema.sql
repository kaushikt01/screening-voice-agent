-- QnA Voice App Database Schema
-- PostgreSQL schema for the voice QnA application

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

-- Create questions table
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    question_text TEXT NOT NULL
);

-- Create answers table
CREATE TABLE IF NOT EXISTS answers (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    answer_audio_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert predefined questions
INSERT INTO questions (id, question_text) VALUES
    (1, 'What is your name?'),
    (2, 'How satisfied are you with our service, from 1 to 5?'),
    (3, 'Would you recommend us to a friend?')
ON CONFLICT (id) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_answers_session_id ON answers(session_id);
CREATE INDEX IF NOT EXISTS idx_answers_question_id ON answers(question_id);
CREATE INDEX IF NOT EXISTS idx_answers_created_at ON answers(created_at);

-- Create a view for easy querying of QnA results
CREATE OR REPLACE VIEW qna_results AS
SELECT 
    s.id as session_id,
    s.created_at as session_created_at,
    q.id as question_id,
    q.question_text,
    a.answer_text,
    a.answer_audio_path,
    a.created_at as answer_created_at
FROM sessions s
JOIN answers a ON s.id = a.session_id
JOIN questions q ON a.question_id = q.id
ORDER BY s.created_at DESC, q.id ASC;
