import numpy as np
from typing import Optional, Tuple
import os

class SileroVAD:
    """
    Lightweight Voice Activity Detection for accurate silence detection
    Uses advanced audio analysis techniques without external model dependencies
    """
    
    def __init__(self):
        self.sample_rate = 16000
        self.threshold = 0.5
        self.min_speech_duration_ms = 250
        self.min_silence_duration_ms = 100
        self.window_size_ms = 30
        self.step_size_ms = 10
        
        # Audio analysis parameters (adjusted for better sensitivity)
        self.energy_threshold = 0.005  # More sensitive to quiet speech
        self.zero_crossing_threshold = 0.05  # Lower threshold for speech detection
        self.spectral_centroid_threshold = 500  # Lower threshold for speech detection
        
    def load_model(self):
        """Initialize VAD (no external model needed)"""
        print("[INFO] Initializing lightweight VAD...")
        print("[INFO] Using advanced audio analysis techniques")
        return True
    
    def preprocess_audio(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Preprocess audio for VAD"""
        # Ensure float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Ensure mono
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=0)
        
        return audio_data
    
    def detect_speech(self, audio_data: np.ndarray, sample_rate: int) -> Tuple[bool, float]:
        """
        Detect if audio contains speech using advanced audio analysis
        Returns: (has_speech, confidence)
        """
        try:
            # Check for empty audio
            if len(audio_data) == 0:
                print("[WARNING] Empty audio data received, treating as silence")
                return False, 0.0
            
            # Preprocess audio
            audio_data = self.preprocess_audio(audio_data, sample_rate)
            
            # Calculate multiple audio features
            energy = self._calculate_energy(audio_data)
            zero_crossing_rate = self._calculate_zero_crossing_rate(audio_data)
            spectral_centroid = self._calculate_spectral_centroid(audio_data, sample_rate)
            
            # Combine features for speech detection
            has_speech = (
                energy > self.energy_threshold and
                zero_crossing_rate > self.zero_crossing_threshold and
                spectral_centroid > self.spectral_centroid_threshold
            )
            
            # Calculate confidence based on feature strengths
            confidence = min(
                (energy / 0.1) * 0.4 +  # Energy contribution
                (zero_crossing_rate / 0.2) * 0.3 +  # Zero crossing contribution
                (spectral_centroid / 2000) * 0.3,  # Spectral centroid contribution
                1.0
            )
            
            return has_speech, confidence
            
        except Exception as e:
            print(f"[ERROR] VAD detection failed: {e}")
            return self._fallback_detect_speech(audio_data, sample_rate)
    
    def _calculate_energy(self, audio_data: np.ndarray) -> float:
        """Calculate signal energy"""
        return np.sqrt(np.mean(audio_data**2))
    
    def _calculate_zero_crossing_rate(self, audio_data: np.ndarray) -> float:
        """Calculate zero crossing rate (indicates frequency content)"""
        if len(audio_data) == 0:
            return 0.0
        zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
        return zero_crossings / len(audio_data)
    
    def _calculate_spectral_centroid(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Calculate spectral centroid (indicates brightness of sound)"""
        try:
            # Simple FFT-based spectral centroid
            fft = np.fft.fft(audio_data)
            magnitude = np.abs(fft)
            frequencies = np.fft.fftfreq(len(audio_data), 1/sample_rate)
            
            # Only positive frequencies
            positive_freq_mask = frequencies > 0
            frequencies = frequencies[positive_freq_mask]
            magnitude = magnitude[positive_freq_mask]
            
            if np.sum(magnitude) == 0:
                return 0.0
            
            spectral_centroid = np.sum(frequencies * magnitude) / np.sum(magnitude)
            return spectral_centroid
        except:
            return 1000.0  # Default value
    
    def _fallback_detect_speech(self, audio_data: np.ndarray, sample_rate: int) -> Tuple[bool, float]:
        """Fallback to simple volume-based speech detection"""
        try:
            # Calculate RMS (Root Mean Square) of audio
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Simple threshold-based detection
            threshold = 0.01  # Adjust this based on your audio levels
            has_speech = rms > threshold
            
            # Convert RMS to confidence (0-1)
            confidence = min(rms * 10, 1.0)  # Scale RMS to confidence
            
            return has_speech, confidence
            
        except Exception as e:
            print(f"[ERROR] Fallback detection failed: {e}")
            return False, 0.0
    
    def is_silence(self, audio_data: np.ndarray, sample_rate: int, min_silence_duration: float = 1.0) -> bool:
        """
        Check if audio contains silence for minimum duration
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Audio sample rate
            min_silence_duration: Minimum silence duration in seconds
        Returns:
            True if silence detected for minimum duration
        """
        try:
            # Check for empty audio
            if len(audio_data) == 0:
                print("[WARNING] Empty audio data received, treating as silence")
                return True
            
            # Preprocess audio
            audio_data = self.preprocess_audio(audio_data, sample_rate)
            
            # Calculate audio features
            energy = self._calculate_energy(audio_data)
            zero_crossing_rate = self._calculate_zero_crossing_rate(audio_data)
            
            # Determine if this audio segment is silent
            is_silent = (
                energy < self.energy_threshold and
                zero_crossing_rate < self.zero_crossing_threshold
            )
            
            # For silence detection, we check if the current segment is silent
            # The duration check is handled by the calling code
            return is_silent
            
        except Exception as e:
            print(f"[ERROR] Silence detection failed: {e}")
            return self._fallback_is_silence(audio_data, sample_rate, min_silence_duration)
    
    def _fallback_is_silence(self, audio_data: np.ndarray, sample_rate: int, min_silence_duration: float = 1.0) -> bool:
        """Fallback to simple volume-based silence detection"""
        try:
            # Calculate RMS of audio
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Simple threshold-based silence detection
            threshold = 0.01  # Adjust this based on your audio levels
            is_silent = rms < threshold
            
            # For fallback, we assume silence if the audio is quiet
            # The duration check is handled by the calling code
            return is_silent
            
        except Exception as e:
            print(f"[ERROR] Fallback silence detection failed: {e}")
            return False
    
    def get_speech_confidence(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """
        Get speech confidence score
        Returns: Confidence score between 0 and 1
        """
        _, confidence = self.detect_speech(audio_data, sample_rate)
        return confidence

# Global instance
vad_instance = SileroVAD()

def get_vad_instance() -> SileroVAD:
    """Get global VAD instance"""
    return vad_instance
