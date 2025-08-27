import os
import requests
import json
from pathlib import Path
from typing import Optional

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "static/audio"))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Azure Cognitive Services configuration
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "eastus")

# Azure TTS endpoint
AZURE_TTS_ENDPOINT = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

# Voice options for Azure TTS
AZURE_VOICES = {
    "en-US-AriaNeural": "Female, friendly and professional",
    "en-US-JennyNeural": "Female, warm and conversational",
    "en-US-GuyNeural": "Male, clear and professional",
    "en-US-DavisNeural": "Male, warm and friendly",
    "en-US-SaraNeural": "Female, energetic and enthusiastic",
    "en-US-TonyNeural": "Male, calm and reassuring",
    "en-US-NancyNeural": "Female, mature and wise",
    "en-US-SteffanNeural": "Male, young and energetic",
    "en-GB-SoniaNeural": "British female, professional",
    "en-GB-RyanNeural": "British male, friendly",
    "en-AU-NatashaNeural": "Australian female, warm",
    "en-AU-WilliamNeural": "Australian male, clear"
}

def generate_tts_azure(
    text: str,
    filename: str,
    voice_name: str = "en-US-AriaNeural",
    rate: str = "+0%",
    pitch: str = "+0%",
    volume: str = "+0%"
) -> str:
    """
    Generate high-quality TTS using Azure Cognitive Services.
    
    Args:
        text: Text to convert to speech
        filename: Output filename
        voice_name: Azure voice name from AZURE_VOICES
        rate: Speech rate (-50% to +50%)
        pitch: Speech pitch (-50% to +50%)
        volume: Speech volume (-50% to +50%)
    """
    if not AZURE_SPEECH_KEY:
        print("Azure Speech key not set. Please set AZURE_SPEECH_KEY environment variable.")
        return ""
    
    try:
        audio_path = AUDIO_DIR / filename
        
        # Prepare SSML (Speech Synthesis Markup Language)
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
                xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
            <voice name="{voice_name}">
                <prosody rate="{rate}" pitch="{pitch}" volume="{volume}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        headers = {
            "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
            "User-Agent": "VoiceAgent"
        }
        
        # Make the API call
        response = requests.post(AZURE_TTS_ENDPOINT, headers=headers, data=ssml.encode('utf-8'))
        response.raise_for_status()
        
        # Save the audio
        with open(audio_path, "wb") as f:
            f.write(response.content)
        
        print(f"Generated Azure TTS audio: {audio_path}")
        return f"/static/audio/{filename}"
        
    except Exception as e:
        print(f"Azure TTS error: {e}")
        return ""

def generate_conversational_azure(
    text: str,
    filename: str,
    personality: str = "friendly"
) -> str:
    """Generate Azure TTS with conversational personality."""
    personality_settings = {
        "friendly": {
            "voice": "en-US-JennyNeural",
            "rate": "+0%",
            "pitch": "+10%",
            "volume": "+0%"
        },
        "professional": {
            "voice": "en-US-AriaNeural",
            "rate": "+0%",
            "pitch": "+0%",
            "volume": "+0%"
        },
        "warm": {
            "voice": "en-US-DavisNeural",
            "rate": "-10%",
            "pitch": "+5%",
            "volume": "+0%"
        },
        "energetic": {
            "voice": "en-US-SaraNeural",
            "rate": "+15%",
            "pitch": "+15%",
            "volume": "+10%"
        },
        "calm": {
            "voice": "en-US-TonyNeural",
            "rate": "-15%",
            "pitch": "-5%",
            "volume": "-5%"
        }
    }
    
    settings = personality_settings.get(personality, personality_settings["friendly"])
    
    return generate_tts_azure(
        text=text,
        filename=filename,
        voice_name=settings["voice"],
        rate=settings["rate"],
        pitch=settings["pitch"],
        volume=settings["volume"]
    )

def generate_emotional_azure(
    text: str,
    filename: str,
    emotion: str = "neutral"
) -> str:
    """Generate Azure TTS with emotional inflection."""
    emotion_settings = {
        "happy": {
            "voice": "en-US-SaraNeural",
            "rate": "+20%",
            "pitch": "+20%",
            "volume": "+15%"
        },
        "excited": {
            "voice": "en-US-SaraNeural",
            "rate": "+25%",
            "pitch": "+25%",
            "volume": "+20%"
        },
        "calm": {
            "voice": "en-US-TonyNeural",
            "rate": "-20%",
            "pitch": "-10%",
            "volume": "-10%"
        },
        "serious": {
            "voice": "en-US-AriaNeural",
            "rate": "-10%",
            "pitch": "-5%",
            "volume": "+0%"
        },
        "neutral": {
            "voice": "en-US-AriaNeural",
            "rate": "+0%",
            "pitch": "+0%",
            "volume": "+0%"
        }
    }
    
    settings = emotion_settings.get(emotion, emotion_settings["neutral"])
    
    return generate_tts_azure(
        text=text,
        filename=filename,
        voice_name=settings["voice"],
        rate=settings["rate"],
        pitch=settings["pitch"],
        volume=settings["volume"]
    )

# Example usage:
# audio_url = generate_tts_azure("Hello, this is a test.", "test_azure.wav")
# conversational = generate_conversational_azure("Great to meet you!", "greeting.wav", "friendly")
# emotional = generate_emotional_azure("That's amazing news!", "excited.wav", "excited")
