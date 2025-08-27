import os
from pathlib import Path
from typing import Optional, Dict, Any
from tts_piper import generate_tts_piper
from tts_elevenlabs import generate_tts_elevenlabs, generate_conversational_voice as elevenlabs_conversational
from tts_azure import generate_tts_azure, generate_conversational_azure as azure_conversational

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "static/audio"))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

class TTSRouter:
    """Smart TTS router that chooses the best available TTS service."""
    
    def __init__(self):
        self.available_services = self._detect_available_services()
        self.preferred_service = self._get_preferred_service()
        print(f"Available TTS services: {list(self.available_services.keys())}")
        print(f"Preferred service: {self.preferred_service}")
    
    def _detect_available_services(self) -> Dict[str, bool]:
        """Detect which TTS services are available."""
        services = {}
        
        # Check ElevenLabs
        services["elevenlabs"] = bool(os.getenv("ELEVENLABS_API_KEY", ""))
        
        # Check Azure
        services["azure"] = bool(os.getenv("AZURE_SPEECH_KEY", ""))
        
        # Check Piper (always available as fallback)
        services["piper"] = True
        
        return services
    
    def _get_preferred_service(self) -> str:
        """Get the preferred TTS service based on quality and availability."""
        if self.available_services.get("elevenlabs"):
            return "elevenlabs"
        elif self.available_services.get("azure"):
            return "azure"
        else:
            return "piper"
    
    def generate_tts(
        self,
        text: str,
        filename: str,
        service: Optional[str] = None,
        personality: str = "friendly",
        emotion: str = "neutral"
    ) -> str:
        """
        Generate TTS using the best available service.
        
        Args:
            text: Text to convert to speech
            filename: Output filename
            service: Specific service to use (optional)
            personality: Voice personality (friendly, professional, warm, etc.)
            emotion: Voice emotion (neutral, happy, excited, calm, serious)
        """
        # Use specified service or preferred service
        target_service = service or self.preferred_service
        
        # Check if target service is available
        if not self.available_services.get(target_service):
            print(f"Service {target_service} not available, falling back to {self.preferred_service}")
            target_service = self.preferred_service
        
        try:
            if target_service == "elevenlabs":
                return elevenlabs_conversational(text, filename, personality)
            elif target_service == "azure":
                return azure_conversational(text, filename, personality)
            else:
                return generate_tts_piper(text, filename)
        except Exception as e:
            print(f"Error with {target_service}: {e}, falling back to Piper")
            return generate_tts_piper(text, filename)
    
    def generate_emotional_tts(
        self,
        text: str,
        filename: str,
        emotion: str = "neutral",
        service: Optional[str] = None
    ) -> str:
        """Generate TTS with specific emotional inflection."""
        target_service = service or self.preferred_service
        
        if not self.available_services.get(target_service):
            target_service = self.preferred_service
        
        try:
            if target_service == "elevenlabs":
                from tts_elevenlabs import generate_emotional_voice
                return generate_emotional_voice(text, filename, emotion)
            elif target_service == "azure":
                from tts_azure import generate_emotional_azure
                return generate_emotional_azure(text, filename, emotion)
            else:
                return generate_tts_piper(text, filename)
        except Exception as e:
            print(f"Error with emotional TTS on {target_service}: {e}, falling back to Piper")
            return generate_tts_piper(text, filename)
    
    def generate_conversational_tts(
        self,
        text: str,
        filename: str,
        personality: str = "friendly",
        service: Optional[str] = None
    ) -> str:
        """Generate conversational TTS with personality."""
        return self.generate_tts(text, filename, service, personality)
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about available TTS services."""
        return {
            "available_services": self.available_services,
            "preferred_service": self.preferred_service,
            "quality_rankings": {
                "elevenlabs": "Professional quality, very natural",
                "azure": "Enterprise quality, clear and natural",
                "piper": "Good quality, open source"
            }
        }

# Global TTS router instance
tts_router = TTSRouter()

# Convenience functions
def generate_tts(text: str, filename: str, **kwargs) -> str:
    """Generate TTS using the best available service."""
    return tts_router.generate_tts(text, filename, **kwargs)

def generate_conversational_voice(text: str, filename: str, personality: str = "friendly", **kwargs) -> str:
    """Generate conversational TTS with personality."""
    return tts_router.generate_conversational_tts(text, filename, personality, **kwargs)

def generate_emotional_voice(text: str, filename: str, emotion: str = "neutral", **kwargs) -> str:
    """Generate TTS with emotional inflection."""
    return tts_router.generate_emotional_tts(text, filename, emotion, **kwargs)

# Example usage:
# audio_url = generate_tts("Hello, this is a test.", "test.wav")
# conversational = generate_conversational_voice("Great to meet you!", "greeting.wav", "friendly")
# emotional = generate_emotional_voice("That's amazing news!", "excited.wav", "excited")
