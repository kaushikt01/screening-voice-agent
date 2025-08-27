import requests
import os
from tts_piper import generate_tts_piper

GEMMA_API_URL = os.getenv("GEMMA_API_URL", "http://192.168.1.6:1234")

def get_gemma_response(prompt: str) -> str:
    """Send prompt to Gemma 3 model and return the generated response text."""
    try:
        response = requests.post(
            f"{GEMMA_API_URL}/v1/chat/completions",
            json={"messages": [{"role": "user", "content": prompt}]}
        )
        response.raise_for_status()
        data = response.json()
        # Adjust parsing based on your Gemma API response format
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Gemma API error: {e}")
        return "Sorry, I couldn't generate a response."

# Example usage:
# response_text = get_gemma_response("What is your name?")
# audio_url = generate_tts_piper(response_text, "question_1.wav")
