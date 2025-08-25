#!/usr/bin/env python3
"""
Simple script to run the QnA Voice App
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting QnA Voice App on {host}:{port}")
    print(f"📱 Open your browser to: http://localhost:{port}/static/index.html")
    print(f"📚 API docs available at: http://localhost:{port}/docs")
    print("=" * 50)
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
