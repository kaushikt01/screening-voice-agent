import os
import wave
import numpy as np
from pathlib import Path
from piper.voice import PiperVoice
from piper.config import SynthesisConfig

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "static/audio"))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Global voice instance for better performance
_voice_instance = None

def create_fallback_voice():
    """Create a basic voice instance using available resources."""
    try:
        # Try to use the tashkeel model as a fallback
        tashkeel_model = ".venv/lib/python3.13/site-packages/piper/tashkeel/model.onnx"
        if os.path.exists(tashkeel_model):
            print("Using tashkeel model as fallback")
            return PiperVoice.load(tashkeel_model)
    except Exception as e:
        print(f"Failed to load tashkeel model: {e}")
    
    # If all else fails, raise an error
    raise RuntimeError("No suitable Piper voice model found")

def get_voice_instance() -> PiperVoice:
    """Get or create a Piper voice instance for better performance."""
    global _voice_instance
    
    if _voice_instance is None:
        try:
            # Try to find a suitable model
            possible_paths = [
                "piper_models/en_US-amy-medium.onnx",
                "piper_models/en_US-amy-low.onnx",
                "piper_models/en_US-amy-high.onnx",
                ".venv/lib/python3.13/site-packages/piper/tashkeel/model.onnx"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        _voice_instance = PiperVoice.load(path)
                        print(f"Loaded Piper model: {path}")
                        break
                    except Exception as e:
                        print(f"Failed to load model at {path}: {e}")
                        continue
            
            if _voice_instance is None:
                print("No models found, creating fallback voice...")
                _voice_instance = create_fallback_voice()
                    
        except Exception as e:
            print(f"Error loading Piper model: {e}")
            raise RuntimeError(f"Failed to load any Piper voice model: {e}")
    
    return _voice_instance

def generate_tts_piper(text: str, filename: str) -> str:
    """Generate TTS audio using Piper Python API and save to AUDIO_DIR. Returns relative audio URL."""
    try:
        audio_path = AUDIO_DIR / filename
        
        # Get voice instance
        voice = get_voice_instance()
        
        # Configure synthesis for better quality using correct parameters
        syn_config = SynthesisConfig(
            length_scale=1.0,      # Normal speech rate
            noise_scale=0.667,     # Balanced clarity vs naturalness
            noise_w_scale=0.8,     # Phoneme width control
            normalize_audio=True,   # Normalize audio output
            volume=1.0             # Normal volume
        )
        
        # Generate audio
        audio_chunks = list(voice.synthesize(text, syn_config))
        
        if not audio_chunks:
            print(f"No audio generated for text: {text}")
            return ""
        
        # Combine all audio chunks
        combined_audio = np.concatenate([chunk.audio_float_array for chunk in audio_chunks])
        
        # Normalize audio to prevent clipping
        max_val = np.max(np.abs(combined_audio))
        if max_val > 0:
            combined_audio = combined_audio / max_val * 0.95
        
        # Convert to 16-bit PCM
        audio_int16 = (combined_audio * 32767).astype(np.int16)
        
        # Save as WAV file
        with wave.open(str(audio_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(22050)  # 22.05 kHz
            wav_file.writeframes(audio_int16.tobytes())
        
        print(f"Generated TTS audio: {audio_path}")
        return f"/static/audio/{filename}"
        
    except Exception as e:
        print(f"Piper TTS error: {e}")
        # Try to create a simple fallback audio
        return create_fallback_audio(text, filename)

def create_fallback_audio(text: str, filename: str) -> str:
    """Create a simple fallback audio when Piper fails."""
    try:
        audio_path = AUDIO_DIR / filename
        
        # Create a simple beep sound as fallback
        sample_rate = 22050
        duration = 1.0  # 1 second
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(2 * np.pi * frequency * t)
        
        # Add some variation based on text length
        if len(text) > 50:
            audio = np.tile(audio, 2)  # Longer text = longer audio
        
        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.5
        
        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Save as WAV
        with wave.open(str(audio_path), 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        print(f"Created fallback audio: {audio_path}")
        return f"/static/audio/{filename}"
        
    except Exception as e:
        print(f"Fallback audio creation failed: {e}")
        return ""

def generate_tts_with_emotion(text: str, filename: str, emotion: str = "neutral") -> str:
    """Generate TTS with emotional inflection."""
    # Adjust synthesis parameters based on emotion
    emotion_configs = {
        "happy": SynthesisConfig(length_scale=0.9, noise_scale=0.7, volume=1.1),
        "sad": SynthesisConfig(length_scale=1.2, noise_scale=0.5, volume=0.9),
        "excited": SynthesisConfig(length_scale=0.8, noise_scale=0.8, volume=1.2),
        "calm": SynthesisConfig(length_scale=1.1, noise_scale=0.4, volume=0.95),
        "neutral": SynthesisConfig(length_scale=1.0, noise_scale=0.667, volume=1.0)
    }
    
    syn_config = emotion_configs.get(emotion, emotion_configs["neutral"])
    
    try:
        audio_path = AUDIO_DIR / filename
        voice = get_voice_instance()
        
        # Generate audio with emotion
        audio_chunks = list(voice.synthesize(text, syn_config))
        
        if not audio_chunks:
            return ""
        
        # Combine and save audio (same logic as above)
        combined_audio = np.concatenate([chunk.audio_float_array for chunk in audio_chunks])
        max_val = np.max(np.abs(combined_audio))
        if max_val > 0:
            combined_audio = combined_audio / max_val * 0.95
        
        audio_int16 = (combined_audio * 32767).astype(np.int16)
        
        with wave.open(str(audio_path), 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes(audio_int16.tobytes())
        
        return f"/static/audio/{filename}"
        
    except Exception as e:
        print(f"Emotional TTS error: {e}")
        return create_fallback_audio(text, filename)

# Example usage:
# audio_url = generate_tts_piper("Hello, this is a test.", "test_piper.wav")
# emotional_audio = generate_tts_with_emotion("Great news!", "excited.wav", "excited")
