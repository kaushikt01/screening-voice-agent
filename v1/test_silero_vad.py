#!/usr/bin/env python3
"""
Test script for Silero VAD
Run this to verify the VAD is working correctly
"""

import numpy as np
import time
from silero_vad import get_vad_instance

def test_silero_vad():
    """Test Silero VAD functionality"""
    print("Testing Silero VAD...")
    
    # Get VAD instance
    vad = get_vad_instance()
    
    # Test 1: Load model
    print("\n1. Testing model loading...")
    if vad.load_model():
        print("✅ Model loaded successfully")
    else:
        print("❌ Model loading failed")
        return False
    
    # Test 2: Create test audio (silence)
    print("\n2. Testing silence detection...")
    sample_rate = 16000
    duration = 2.0  # 2 seconds
    silence_audio = np.zeros(int(sample_rate * duration), dtype=np.float32)
    
    is_silent = vad.is_silence(silence_audio, sample_rate, min_silence_duration=1.0)
    print(f"Silence audio detected as silent: {is_silent}")
    
    # Test 3: Create test audio (noise)
    print("\n3. Testing speech detection...")
    noise_audio = np.random.randn(int(sample_rate * duration)).astype(np.float32) * 0.1
    
    has_speech, confidence = vad.detect_speech(noise_audio, sample_rate)
    print(f"Noise audio - Has speech: {has_speech}, Confidence: {confidence:.3f}")
    
    # Test 4: Performance test
    print("\n4. Testing performance...")
    start_time = time.time()
    
    for i in range(10):
        vad.detect_speech(silence_audio, sample_rate)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10
    print(f"Average processing time: {avg_time:.3f} seconds")
    
    print("\n✅ Silero VAD test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        test_silero_vad()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\nMake sure you have installed the dependencies:")
        print("pip install torch torchaudio numpy")
