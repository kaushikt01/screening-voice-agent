import os
import requests
import json
from pathlib import Path
from typing import Optional

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "static/audio"))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ElevenLabs configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

# Voice IDs for different personalities
VOICE_IDS = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",      # Professional, friendly female
    "domi": "AZnzlk1XvdvUeBnXmlld",        # Warm, conversational female
    "bella": "EXAVITQu4vr4xnSDxMaL",        # Clear, articulate female
    "antoni": "ErXwobaYiN1PXXYvJEWp",       # Professional male
    "thomas": "GBv7mTt0atIp3Br8iCZE",       # Warm, friendly male
    "josh": "TxGEqnHWrfWFTfGW9XjX",         # Clear, professional male
    "arnold": "VR6AewLTigWG4xSOukaG",       # Deep, authoritative male
    "sam": "yoZ06aMxZJJ28mfd3POQ",          # Young, energetic male
    "dorothy": "ThT5KcBeYPX3keUQqHPh",      # Mature, wise female
    "clyde": "2EiwWnXFnvU5JabPnv8n",        # Casual, friendly male
}

def get_available_voices() -> list:
    """Get list of available voices from ElevenLabs."""
    if not ELEVENLABS_API_KEY:
        return []
    
    try:
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        response = requests.get(f"{ELEVENLABS_BASE_URL}/voices", headers=headers)
        response.raise_for_status()
        return response.json().get("voices", [])
    except Exception as e:
        print(f"Error fetching voices: {e}")
        return []

def generate_tts_elevenlabs(
    text: str, 
    filename: str, 
    voice_id: str = "rachel",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    style: float = 0.0,
    use_speaker_boost: bool = True
) -> str:
    """
    Generate high-quality TTS using ElevenLabs API.
    
    Args:
        text: Text to convert to speech
        filename: Output filename
        voice_id: Voice ID from VOICE_IDS or custom ID
        stability: Voice stability (0-1, lower = more expressive)
        similarity_boost: Voice similarity (0-1, higher = more similar to original)
        style: Style exaggeration (0-1, higher = more dramatic)
        use_speaker_boost: Enhance speaker clarity
    """
    if not ELEVENLABS_API_KEY:
        print("ElevenLabs API key not set. Please set ELEVENLABS_API_KEY environment variable.")
        return ""
    
    try:
        audio_path = AUDIO_DIR / filename
        
        # Prepare the request
        url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Best quality model
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": use_speaker_boost
            }
        }
        
        # Make the API call
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # Save the audio
        with open(audio_path, "wb") as f:
            f.write(response.content)
        
        print(f"Generated ElevenLabs TTS audio: {audio_path}")
        return f"/static/audio/{filename}"
        
    except Exception as e:
        print(f"ElevenLabs TTS error: {e}")
        return ""

def generate_conversational_voice(text: str, filename: str, personality: str = "friendly") -> str:
    """Generate voice with specific conversational personality."""
    personality_settings = {
        "friendly": {
            "voice_id": "domi",
            "stability": 0.4,
            "similarity_boost": 0.8,
            "style": 0.2,
            "use_speaker_boost": True
        },
        "professional": {
            "voice_id": "rachel",
            "stability": 0.6,
            "similarity_boost": 0.9,
            "style": 0.0,
            "use_speaker_boost": True
        },
        "warm": {
            "voice_id": "bella",
            "stability": 0.5,
            "similarity_boost": 0.85,
            "style": 0.1,
            "use_speaker_boost": True
        },
        "energetic": {
            "voice_id": "sam",
            "stability": 0.3,
            "similarity_boost": 0.7,
            "style": 0.4,
            "use_speaker_boost": True
        },
        "authoritative": {
            "voice_id": "arnold",
            "stability": 0.7,
            "similarity_boost": 0.95,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    settings = personality_settings.get(personality, personality_settings["friendly"])
    
    return generate_tts_elevenlabs(
        text=text,
        filename=filename,
        voice_id=settings["voice_id"],
        stability=settings["stability"],
        similarity_boost=settings["similarity_boost"],
        style=settings["style"],
        use_speaker_boost=settings["use_speaker_boost"]
    )

def generate_emotional_voice(text: str, filename: str, emotion: str = "neutral") -> str:
    """Generate voice with emotional inflection."""
    emotion_settings = {
        "happy": {
            "voice_id": "domi",
            "stability": 0.3,
            "similarity_boost": 0.7,
            "style": 0.6,
            "use_speaker_boost": True
        },
        "excited": {
            "voice_id": "sam",
            "stability": 0.2,
            "similarity_boost": 0.6,
            "style": 0.8,
            "use_speaker_boost": True
        },
        "calm": {
            "voice_id": "bella",
            "stability": 0.8,
            "similarity_boost": 0.9,
            "style": 0.0,
            "use_speaker_boost": True
        },
        "serious": {
            "voice_id": "arnold",
            "stability": 0.9,
            "similarity_boost": 0.95,
            "style": 0.0,
            "use_speaker_boost": True
        },
        "neutral": {
            "voice_id": "rachel",
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    settings = emotion_settings.get(emotion, emotion_settings["neutral"])
    
    return generate_tts_elevenlabs(
        text=text,
        filename=filename,
        voice_id=settings["voice_id"],
        stability=settings["stability"],
        similarity_boost=settings["similarity_boost"],
        style=settings["style"],
        use_speaker_boost=settings["use_speaker_boost"]
    )

# Example usage:
# audio_url = generate_tts_elevenlabs("Hello, this is a test.", "test_elevenlabs.wav")
# conversational = generate_conversational_voice("Great to meet you!", "greeting.wav", "friendly")
# emotional = generate_emotional_voice("That's amazing news!", "excited.wav", "excited")
