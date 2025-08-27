import os
from pathlib import Path
import subprocess
import random

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "static/audio"))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def generate_tts_coqui(text: str, filename: str, speaker: str = "tts_models/en/vctk/vits", lang: str = "en") -> str:
    """Generate TTS audio using Coqui VITS model and save to AUDIO_DIR. Returns relative audio URL."""
    # Add punctuation for more natural prosody
    if not text.endswith('.'):
        text = text.strip() + '.'
    audio_path = AUDIO_DIR / filename
    if not audio_path.exists():
        # Randomize speaker_idx for more natural voice (VCTK: 0-108)
        speaker_idx = random.randint(0, 108)
        cmd = [
            "tts",
            "--text", text,
            "--model_name", speaker,
            "--out_path", str(audio_path),
            "--speaker_idx", str(speaker_idx)
        ]
        try:
            subprocess.run(cmd, check=True)
        except Exception as e:
            print(f"Coqui TTS error: {e}")
            return ""
    return f"/static/audio/{filename}"

# Example usage:
# audio_url = generate_tts_coqui("Hello, this is a test.", "test_coqui.wav")
