# TTS Service Setup Guide

This guide will help you set up high-quality, natural-sounding Text-to-Speech services that sound like ChatGPT or Gemini.

## 🎯 Voice Quality Rankings

1. **ElevenLabs** - ⭐⭐⭐⭐⭐ Professional quality, very natural (ChatGPT-like)
2. **Azure Cognitive Services** - ⭐⭐⭐⭐ Enterprise quality, clear and natural
3. **Piper TTS** - ⭐⭐⭐ Good quality, open source (current fallback)

## 🚀 Quick Start - ElevenLabs (Recommended)

ElevenLabs provides the most natural, ChatGPT-like voices available.

### Step 1: Get API Key
1. Go to [ElevenLabs.io](https://elevenlabs.io/)
2. Sign up for a free account
3. Go to your profile → API Key
4. Copy your API key

### Step 2: Set Environment Variable
```bash
export ELEVENLABS_API_KEY="your_api_key_here"
```

Or add to your `.env` file:
```
ELEVENLABS_API_KEY=your_api_key_here
```

### Step 3: Test
The system will automatically detect and use ElevenLabs for the best voice quality.

## 🏢 Azure Cognitive Services (Alternative)

Microsoft's enterprise-grade TTS service with very natural voices.

### Step 1: Get Azure Keys
1. Go to [Azure Portal](https://portal.azure.com/)
2. Create a Speech Service resource
3. Get your key and region from the resource

### Step 2: Set Environment Variables
```bash
export AZURE_SPEECH_KEY="your_azure_key_here"
export AZURE_SPEECH_REGION="eastus"
```

## 🔧 Manual Configuration

### Option 1: Environment Variables
```bash
# Set these in your shell or .env file
export ELEVENLABS_API_KEY="your_key"
export AZURE_SPEECH_KEY="your_key"
export AZURE_SPEECH_REGION="eastus"
```

### Option 2: .env File
Create a `.env` file in the `v1/` directory:
```env
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=eastus
```

## 🎭 Voice Personalities

The system automatically selects the best voice for different scenarios:

### Conversational Personalities
- **Friendly** - Warm, approachable voice
- **Professional** - Clear, business-like voice
- **Warm** - Gentle, caring voice
- **Energetic** - Excited, enthusiastic voice
- **Authoritative** - Confident, leadership voice

### Emotional Inflections
- **Happy** - Joyful, upbeat tone
- **Excited** - Energetic, enthusiastic
- **Calm** - Soothing, relaxed
- **Serious** - Focused, determined
- **Neutral** - Balanced, clear

## 🧪 Testing Your Setup

### Test ElevenLabs
```python
from tts_elevenlabs import generate_tts_elevenlabs
audio_url = generate_tts_elevenlabs("Hello, this is a test of ElevenLabs!", "test.wav")
```

### Test Azure
```python
from tts_azure import generate_tts_azure
audio_url = generate_tts_azure("Hello, this is a test of Azure TTS!", "test.wav")
```

### Test Router (Recommended)
```python
from tts_router import generate_tts
audio_url = generate_tts("Hello, this is a test!", "test.wav")
```

## 💰 Cost Information

### ElevenLabs
- **Free Tier**: 10,000 characters/month
- **Paid Plans**: Starting at $5/month for 30,000 characters
- **Quality**: Professional, ChatGPT-like voices

### Azure
- **Free Tier**: 500,000 characters/month
- **Paid Plans**: $16 per 1 million characters
- **Quality**: Enterprise-grade, very natural

### Piper TTS
- **Cost**: Free (open source)
- **Quality**: Good, but not as natural as paid services

## 🚨 Troubleshooting

### "API key not set" Error
- Check that your environment variables are set correctly
- Restart your terminal/application after setting variables
- Verify the API key is valid

### "Service not available" Error
- The system will automatically fall back to Piper TTS
- Check your internet connection
- Verify API quotas haven't been exceeded

### Poor Voice Quality
- Ensure you're using ElevenLabs or Azure (not Piper fallback)
- Check that the correct service is being used
- Try different voice personalities

## 🔄 Automatic Fallback

The system automatically handles service failures:

1. **Primary**: ElevenLabs (if available)
2. **Secondary**: Azure (if available)
3. **Fallback**: Piper TTS (always available)

## 📱 Integration

The new TTS system is automatically integrated into:
- Introduction messages
- Question generation
- All voice responses

No code changes needed - just set your API keys!

## 🎉 Result

With ElevenLabs or Azure configured, you'll get:
- ✅ Natural, ChatGPT-like voices
- ✅ Emotional inflection
- ✅ Multiple personality types
- ✅ Professional quality audio
- ✅ Automatic fallback handling

Your voice agent will sound like a real human, not a robotic TTS system!
