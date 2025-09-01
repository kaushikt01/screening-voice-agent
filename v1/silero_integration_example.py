"""
Example: How to integrate Silero VAD into your existing CallInterface

This shows how to replace the current WebAudio silence detection with Silero VAD
for more accurate silence detection.
"""

# 1. Install dependencies
# pip install torch torchaudio numpy

# 2. Import Silero VAD
from silero_vad import get_vad_instance
import numpy as np
import wave
import io

# 3. Example integration with your existing recording system
class SileroVADIntegration:
    def __init__(self):
        self.vad = get_vad_instance()
        self.silence_threshold = 1.5  # seconds of silence to trigger stop
    
    def process_audio_chunk(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        """
        Process audio chunk and detect if it contains silence
        Returns: True if silence detected for threshold duration
        """
        try:
            # Convert audio chunk to numpy array
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Use Silero VAD to detect silence
            is_silent = self.vad.is_silence(
                audio_data, 
                sample_rate, 
                min_silence_duration=self.silence_threshold
            )
            
            return is_silent
            
        except Exception as e:
            print(f"[ERROR] VAD processing failed: {e}")
            return False
    
    def get_speech_confidence(self, audio_chunk: bytes, sample_rate: int = 16000) -> float:
        """
        Get speech confidence for audio chunk
        Returns: Confidence score between 0 and 1
        """
        try:
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            return self.vad.get_speech_confidence(audio_data, sample_rate)
        except Exception as e:
            print(f"[ERROR] Speech confidence detection failed: {e}")
            return 0.0

# 4. Integration with your existing CallInterface
"""
In your CallInterface.tsx, you would:

1. Send audio chunks to backend for VAD processing
2. Replace the current WebAudio silence detection
3. Use Silero VAD results to determine when to stop recording

Example API endpoint to add to app.py:

@app.post("/api/vad-detect")
async def vad_detect_silence(audio_chunk: bytes = File(...)):
    try:
        vad_integration = SileroVADIntegration()
        is_silent = vad_integration.process_audio_chunk(audio_chunk)
        confidence = vad_integration.get_speech_confidence(audio_chunk)
        
        return {
            "is_silent": is_silent,
            "speech_confidence": confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

Example frontend integration:

// In your startSilenceDetection function, replace WebAudio with:
const processAudioChunk = async (audioChunk: Blob) => {
    const formData = new FormData();
    formData.append('audio_chunk', audioChunk);
    
    const response = await fetch('/api/vad-detect', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    
    if (result.is_silent) {
        console.log('Silero VAD detected silence, stopping recording');
        stopRecording();
    }
};
"""

# 5. Benefits of using Silero VAD
benefits = """
Benefits of Silero VAD over current WebAudio approach:

✅ More Accurate: Better at distinguishing speech from background noise
✅ Configurable: Adjustable sensitivity and duration thresholds  
✅ Robust: Handles various audio conditions and environments
✅ Fast: Efficient processing with minimal latency
✅ Free: No API costs or usage limits
✅ Offline: Works completely offline

Current WebAudio Issues:
❌ Basic volume-based detection
❌ Sensitive to background noise
❌ No speech vs noise distinction
❌ Limited configurability
"""

if __name__ == "__main__":
    print("Silero VAD Integration Example")
    print("=" * 40)
    print(benefits)
    print("\nTo integrate:")
    print("1. Install dependencies: pip install torch torchaudio numpy")
    print("2. Add the VAD endpoint to your app.py")
    print("3. Update your frontend to use the VAD API")
    print("4. Replace WebAudio silence detection with Silero VAD")
