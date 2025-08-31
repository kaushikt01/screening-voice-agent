# TTS Setup Guide

This guide helps you set up Text-to-Speech (TTS) functionality for the QnA Voice Agent.

## Quick Setup

### 1. Install Dependencies

```bash
# Activate your virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install TTS dependencies
pip install piper-tts torch torchaudio
```

### 2. Download Piper Models

The app uses Piper TTS for high-quality speech synthesis. You need to download voice models:

```bash
# Create models directory
mkdir -p piper_models

# Download a voice model (example: Amy voice)
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx -O piper_models/en_US-amy-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json -O piper_models/en_US-amy-medium.onnx.json
```

### 3. Alternative: Use pipx (Recommended)

For easier installation:

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install piper-tts globally
pipx install piper-tts

# Download models using piper-tts
piper-tts --download en_US-amy-medium
```

## Troubleshooting

### ModuleNotFoundError: No module named 'piper'

This error occurs when the `piper-tts` package isn't installed correctly.

**Solution:**
```bash
# Make sure you're in your virtual environment
source .venv/bin/activate

# Uninstall and reinstall
pip uninstall piper-tts
pip install piper-tts

# Or try installing from source
pip install git+https://github.com/rhasspy/piper.git
```

### Model Loading Issues

If you get errors loading the voice models:

1. **Check model files exist:**
   ```bash
   ls -la piper_models/
   ```

2. **Verify model integrity:**
   ```bash
   # The .onnx and .json files should be present
   # .onnx file should be several MB
   # .json file should be a few KB
   ```

3. **Download fresh models:**
   ```bash
   rm piper_models/*
   # Then re-download using the commands above
   ```

### Performance Issues

For better performance:

1. **Use GPU acceleration (if available):**
   ```bash
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

2. **Use smaller models for faster generation:**
   ```bash
   # Download low-quality but fast model
   wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/low/en_US-amy-low.onnx -O piper_models/en_US-amy-low.onnx
   wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/low/en_US-amy-low.onnx.json -O piper_models/en_US-amy-low.onnx.json
   ```

## Available Voice Models

You can download different voice models from:
- **Amy (Female, US English):** `en_US-amy-medium`
- **Jenny (Female, US English):** `en_US-jenny-medium`
- **Mike (Male, US English):** `en_US-mike-medium`

Download URLs: https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0/en/en_US

## Testing TTS

After setup, test the TTS functionality:

```bash
# Run the app
python run.py

# In another terminal, test TTS endpoint
curl -X POST "http://localhost:8000/api/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test.", "filename": "test.wav"}'
```

## Fallback Options

If Piper TTS continues to have issues, the app includes fallback TTS options:

1. **Coqui TTS** (already in requirements)
2. **Azure TTS** (requires API key)
3. **ElevenLabs TTS** (requires API key)

Configure these in your `.env` file and update `tts_router.py` as needed.
