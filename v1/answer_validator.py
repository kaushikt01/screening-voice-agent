import re
from typing import Dict, List, Optional, Tuple
from tts_utils import get_gemma_response

class AnswerValidator:
    """
    Validates user answers using local LLM to ensure they are in context
    and provides fallback responses when validation fails.
    """
    
    def __init__(self):
        # Dynamic validation system that adapts to any question type
        self.base_validation_prompt = """You are a strict answer validator. Your job is to determine if a user's response is appropriate and complete for the given question.

Question: "{question}"
User's response: "{answer}"

Analyze the response considering:
1. Does it directly answer the question asked?
2. Is it complete and specific enough?
3. Does it contain the required information?
4. Is it a reasonable response (not gibberish, off-topic, or evasive)?

IMPORTANT: Be very strict. If the response doesn't clearly and directly answer the question, mark it as INVALID.

Examples of INVALID responses:
- "I don't know" -> INVALID
- "Hello there" -> INVALID  
- "How are you?" -> INVALID
- "Can you repeat that?" -> INVALID
- "Maybe" -> INVALID
- "I'm not sure" -> INVALID
- Any response that doesn't directly answer the question

Respond with ONLY:
- "VALID" if the response clearly and directly answers the question
- "INVALID" if the response is incomplete, off-topic, evasive, unclear, or doesn't answer the question

Be very strict - if in doubt, mark as INVALID."""

        # Dynamic fallback message generator
        self.fallback_templates = {
            "name": "I need your full name - first and last name. Could you please provide both?",
            "ssn": "I need your Social Security Number to proceed. Please provide your 9-digit SSN.",
            "address": "I need your complete address including street number, street name, and ZIP code.",
            "yes_no": "I need a clear yes or no answer to this question. Please respond with yes or no.",
            "date": "I need the date in MM/DD/YYYY format. Please provide the date in this format.",
            "default": "I didn't understand your response. Could you please answer the question clearly?"
        }
    
    async def validate_answer(self, question_id: int, question_text: str, answer_text: str) -> Tuple[bool, str]:
        """
        Validate if the answer is appropriate for the question using dynamic LLM validation.
        Returns (is_valid, fallback_message)
        """
        try:
            # For now, use simple validation logic to test the system
            # TODO: Re-enable LLM validation once we debug the issue
            is_valid = self._simple_validation(question_id, question_text, answer_text)
            print(f"[DEBUG] Simple validation result: {is_valid}")
            
            # Generate dynamic fallback message
            fallback_message = self._generate_dynamic_fallback(question_id, question_text, answer_text, is_valid)
            
            return is_valid, fallback_message if not is_valid else ""
            
        except Exception as e:
            print(f"[ERROR] Answer validation failed: {e}")
            # If validation fails, assume answer is valid to avoid blocking the flow
            return True, ""
    
    def _simple_validation(self, question_id: int, question_text: str, answer_text: str) -> bool:
        """Simple validation logic for testing."""
        answer_lower = answer_text.lower().strip()
        
        # Common invalid responses
        invalid_phrases = [
            "i don't know", "i dont know", "don't know", "dont know",
            "i'm not sure", "im not sure", "not sure", "unsure",
            "maybe", "perhaps", "i think", "i guess",
            "what do you mean", "can you repeat", "repeat",
            "hello", "hi", "hey", "goodbye", "bye",
            "how are you", "nice to meet you", "thank you"
        ]
        
        # Check for invalid phrases
        for phrase in invalid_phrases:
            if phrase in answer_lower:
                return False
        
        # For name questions, check if it has at least 2 words
        if question_id == 1 or "name" in question_text.lower():
            words = answer_text.split()
            if len(words) < 2:
                return False
        
        # For SSN questions, check for 9 digits
        if question_id == 2 or "social security" in question_text.lower():
            digits = ''.join(filter(str.isdigit, answer_text))
            if len(digits) != 9:
                return False
        
        # For yes/no questions, check for clear yes/no
        if "yes or no" in question_text.lower() or "answer yes or no" in question_text.lower():
            if not any(word in answer_lower for word in ["yes", "no", "yeah", "nope", "yep", "nah"]):
                return False
        
        return True
    
    def _get_question_type(self, question_id: int, question_text: str) -> str:
        """Determine the type of question based on ID and text."""
        question_text_lower = question_text.lower()
        
        # Name question (usually first question)
        if question_id == 1 or "name" in question_text_lower:
            return "name"
        
        # SSN question
        elif question_id == 2 or "social security" in question_text_lower or "ssn" in question_text_lower:
            return "ssn"
        
        # Address question
        elif question_id == 3 or "address" in question_text_lower or "zip" in question_text_lower:
            return "address"
        
        # Date questions (hire date, start date)
        elif question_id in [12, 13] or "date" in question_text_lower:
            return "date"
        
        # Yes/No questions (most other questions)
        elif "yes or no" in question_text_lower or "answer yes or no" in question_text_lower:
            return "yes_no"
        
        # Default to yes/no for most questions
        else:
            return "yes_no"
    
    def _generate_dynamic_fallback(self, question_id: int, question_text: str, answer_text: str, is_valid: bool) -> str:
        """Generate dynamic fallback message based on question context and validation result."""
        try:
            # Use template-based fallback to avoid multiple LLM calls
            question_type = self._get_question_type(question_id, question_text)
            return self.fallback_templates.get(question_type, self.fallback_templates["default"])
            
        except Exception as e:
            print(f"[ERROR] Dynamic fallback generation failed: {e}")
            return self.fallback_templates["default"]

    def get_validation_fallback_audio(self, question_id: int, question_text: str) -> str:
        """Generate fallback audio for validation failures."""
        question_type = self._get_question_type(question_id, question_text)
        return self.fallback_templates.get(question_type, self.fallback_templates["default"])
