# MongoDB Setup for QnA Voice Application

This guide will help you set up MongoDB for the QnA Voice application.

## Prerequisites

1. **MongoDB Installation**
   - Install MongoDB Community Edition on your system
   - For macOS: `brew install mongodb-community`
   - For Ubuntu: Follow [MongoDB installation guide](https://docs.mongodb.com/manual/installation/)
   - For Windows: Download from [MongoDB website](https://www.mongodb.com/try/download/community)

2. **Python Dependencies**
   ```bash
   pip install motor pymongo
   ```

## Quick Setup

### 1. Start MongoDB Service

**macOS:**
```bash
brew services start mongodb-community
```

**Ubuntu:**
```bash
sudo systemctl start mongod
```

**Windows:**
```bash
# MongoDB should start automatically as a service
```

### 2. Test Connection

```bash
python setup_mongodb.py test
```

### 3. Initialize Database

```bash
python setup_mongodb.py init
```

### 4. Verify Setup

```bash
python setup_mongodb.py all
```

## Database Schema

The application uses the following MongoDB collections:

### 1. `sessions` Collection
```json
{
  "_id": "ObjectId",
  "id": "string (unique session identifier)",
  "client_id": "string (optional)",
  "created_at": "datetime",
  "status": "string (active/completed/abandoned)",
  "metadata": "object (additional session data)"
}
```

### 2. `questions` Collection
```json
{
  "_id": "ObjectId",
  "id": "integer (unique question identifier)",
  "question_text": "string",
  "category": "string (personal_info/eligibility/general)",
  "is_required": "boolean",
  "order": "integer (question sequence)",
  "metadata": "object (additional question data)"
}
```

### 3. `answers` Collection
```json
{
  "_id": "ObjectId",
  "session_id": "string (references sessions.id)",
  "question_id": "integer (references questions.id)",
  "answer_text": "string (transcribed answer)",
  "answer_audio_path": "string (path to audio file)",
  "confidence_score": "float (transcription confidence)",
  "processing_time_ms": "integer (processing duration)",
  "created_at": "datetime",
  "metadata": "object (additional answer data)"
}
```

### 4. `analytics` Collection
```json
{
  "_id": "ObjectId",
  "session_id": "string (references sessions.id)",
  "question_id": "integer (references questions.id)",
  "response_time_ms": "integer",
  "answer_duration_ms": "integer",
  "audio_quality_score": "float (0-1)",
  "confidence_score": "float (0-1)",
  "hesitation_detected": "boolean",
  "completed": "boolean",
  "timestamp": "datetime",
  "metadata": "object (additional analytics data)"
}
```

## Environment Variables

Set these environment variables for MongoDB connection:

```bash
export MONGODB_URL="mongodb://localhost:27017"
export DATABASE_NAME="qna_voice"
```

Or create a `.env` file:
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=qna_voice
```

## Default Questions

The application comes with 7 predefined questions for WOTC eligibility:

1. **Name Collection** - "Let's get started with your name—what's your first and last name?"
2. **SSN Collection** - "Please share your Social Security Number. If you'd rather skip for now, just say 'skip'."
3. **Address Collection** - "What's your street address, including ZIP code?"
4. **Age Verification** - "Are you under the age of 40?"
5. **Welfare Verification** - "Have you or anyone in your household received TANF welfare payments?"
6. **Military Service** - "Have you served in the U.S. military?"
7. **Unemployment Verification** - "In the past year, were you unemployed and did you receive unemployment compensation for at least 27 weeks?"

## Troubleshooting

### Connection Issues
```bash
# Check if MongoDB is running
ps aux | grep mongod

# Check MongoDB logs
tail -f /var/log/mongodb/mongod.log

# Test connection manually
mongosh
```

### Database Issues
```bash
# View database status
python setup_mongodb.py health

# View questions
python setup_mongodb.py questions

# View recent sessions
python setup_mongodb.py sessions

# View recent answers
python setup_mongodb.py answers
```

### Reset Database
```bash
# Connect to MongoDB shell
mongosh

# Switch to database
use qna_voice

# Drop all collections
db.sessions.drop()
db.questions.drop()
db.answers.drop()
db.analytics.drop()

# Reinitialize
python setup_mongodb.py init
```

## Performance Optimization

### Indexes
The application automatically creates the following indexes for optimal performance:

- `sessions.id` (unique)
- `sessions.created_at`
- `sessions.status`
- `questions.id` (unique)
- `questions.order`
- `questions.category`
- `answers.session_id`
- `answers.question_id`
- `answers.created_at`
- `answers.session_id + question_id` (unique compound index)
- `analytics.session_id`
- `analytics.question_id`
- `analytics.timestamp`

### Connection Pooling
The application uses Motor (async MongoDB driver) with connection pooling for optimal performance.

## Security Considerations

1. **Authentication**: For production, enable MongoDB authentication
2. **Network Security**: Restrict MongoDB to localhost or use VPN
3. **Data Encryption**: Enable MongoDB encryption at rest
4. **Backup**: Set up regular database backups

## Production Deployment

For production deployment:

1. **Use MongoDB Atlas** (cloud service) or **MongoDB Enterprise**
2. **Enable authentication and authorization**
3. **Set up monitoring and alerting**
4. **Configure automated backups**
5. **Use connection string with credentials**:
   ```
   MONGODB_URL=mongodb://username:password@host:port/database?authSource=admin
   ```
