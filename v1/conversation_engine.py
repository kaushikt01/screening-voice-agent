import random
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

class ConversationEngine:
    """
    Dynamic conversation engine that makes the voice agent behave like ChatGPT.
    Instead of rigid IVR questions, it creates natural, flowing conversations.
    """
    
    def __init__(self):
        # Core conversation topics and their variations
        self.conversation_topics = {
            "name": {
                "main_question": "What's your first and last name?",
                "variations": [
                    "Let's get started with your name—what's your first and last name?",
                    "Could you please tell me your full name—first and last?",
                    "To begin, may I have your first and last name?",
                    "What should I call you? Please share your first and last name.",
                    "I'd love to know your name—first and last, please."
                ],
                "follow_ups": [
                    "Thanks! Next, I'll ask for a few details.",
                    "Perfect, got it. I'll grab a couple more details.",
                    "Great, thank you. I'll keep it quick."
                ],
                "contextual_questions": [
                    "Thanks for that. Are you comfortable sharing a few more details?",
                    "Appreciate it. I'll just ask a couple more simple questions.",
                    "Got it. Let's continue with the next detail."
                ]
            },
            "ssn": {
                "main_question": "Please share your Social Security Number.",
                "variations": [
                    "Please share your Social Security Number. If you'd rather skip for now, just say 'skip'.",
                    "Could you provide your SSN? You can say 'skip' if you prefer not to share it right now.",
                    "What is your Social Security Number? You're welcome to say 'skip'.",
                    "If you're comfortable, please provide your SSN; otherwise say 'skip'."
                ],
                "follow_ups": [
                    "Thanks. Let's confirm your address next.",
                    "Appreciate it. I'll move to your mailing address next.",
                    "Got it. Next, I'll ask for your address."
                ],
                "contextual_questions": [
                    "Thanks. Is it okay if I proceed with your address?",
                    "Understood. I'll go ahead and ask for your address details.",
                    "Thank you. Let's continue with your address."
                ]
            },
            "address": {
                "main_question": "What's your street address, including ZIP code?",
                "variations": [
                    "What's your street address, including ZIP code?",
                    "Could you share your full mailing address with ZIP code?",
                    "Please provide your street address and ZIP code.",
                    "What address should I keep on file, with ZIP code?"
                ],
                "follow_ups": [
                    "Thanks. I'll ask about cash assistance next.",
                    "Perfect, thank you. Next is about cash assistance benefits.",
                    "Great. I have a question about cash assistance next."
                ],
                "contextual_questions": [
                    "Appreciate that. Shall we continue?",
                    "Thanks! Ready for the next question?",
                    "Got it. I'll keep it moving."
                ]
            },
            "cash_assistance": {
                "main_question": "Have you or a household family member received any form of cash assistance (A.F.D.C. and T.A.N.F. benefits) within the last two years? Please answer YES or NO.",
                "variations": [
                    "Have you or a household family member received any form of cash assistance (A.F.D.C. and T.A.N.F. benefits) within the last two years? Please answer YES or NO.",
                    "Within the last two years, have you or anyone in your household received A.F.D.C. or T.A.N.F. benefits? Please answer YES or NO.",
                    "Have you or a family member received cash assistance benefits in the past two years? Please answer YES or NO."
                ],
                "follow_ups": [
                    "Thank you. Next, I'll ask about eligibility limitations.",
                    "Got it. I'll ask about eligibility limitations next.",
                    "Thanks. Moving on to eligibility limitations."
                ],
                "contextual_questions": [
                    "Appreciate that. Ready for the next one?",
                    "Thanks for clarifying. Let's continue.",
                    "Understood. I'll keep this brief."
                ]
            },
            "eligibility_limitation": {
                "main_question": "Are you a member of a family that stopped being eligible for cash assistance (A.F.D.C. or T.A.N.F. benefits) within the last two years because of federal or state limitations? Please answer YES or NO.",
                "variations": [
                    "Are you a member of a family that stopped being eligible for cash assistance (A.F.D.C. or T.A.N.F. benefits) within the last two years because of federal or state limitations? Please answer YES or NO.",
                    "Did your family stop being eligible for cash assistance benefits in the last two years due to federal or state limitations? Please answer YES or NO.",
                    "Within the last two years, did your family lose eligibility for A.F.D.C. or T.A.N.F. benefits due to federal or state limitations? Please answer YES or NO."
                ],
                "follow_ups": [
                    "Thank you. Next, I'll ask about other assistance programs.",
                    "Got it. I'll ask about other assistance next.",
                    "Thanks. Moving on to other assistance programs."
                ],
                "contextual_questions": [
                    "Appreciate that. Ready for the next one?",
                    "Thanks for clarifying. Let's continue.",
                    "Understood. I'll keep this brief."
                ]
            },
            "other_assistance": {
                "main_question": "Have you received any child care, housing or transportation assistance anytime since 18 months ago? Please answer YES or NO.",
                "variations": [
                    "Have you received any child care, housing or transportation assistance anytime since 18 months ago? Please answer YES or NO.",
                    "Since 18 months ago, have you received any child care, housing, or transportation assistance? Please answer YES or NO.",
                    "Have you received assistance with child care, housing, or transportation in the last 18 months? Please answer YES or NO."
                ],
                "follow_ups": [
                    "Thank you. Next, I'll ask about criminal history.",
                    "Got it. I'll ask about criminal history next.",
                    "Thanks. Moving on to criminal history questions."
                ],
                "contextual_questions": [
                    "Appreciate that. Ready for the next one?",
                    "Thanks for clarifying. Let's continue.",
                    "Understood. I'll keep this brief."
                ]
            },
            "felony": {
                "main_question": "Have you ever been convicted of a felony or received deferred adjudication for a felony charge? Please answer YES or NO.",
                "variations": [
                    "Have you ever been convicted of a felony or received deferred adjudication for a felony charge? Please answer YES or NO.",
                    "Have you ever been convicted of a felony or received deferred adjudication? Please answer YES or NO.",
                    "Do you have any felony convictions or deferred adjudication? Please answer YES or NO."
                ],
                "follow_ups": [
                    "Thank you. Next, I'll ask about vocational rehabilitation.",
                    "Got it. I'll ask about vocational rehabilitation next.",
                    "Thanks. Moving on to vocational rehabilitation."
                ],
                "contextual_questions": [
                    "Appreciate that. Ready for the next one?",
                    "Thanks for clarifying. Let's continue.",
                    "Understood. I'll keep this brief."
                ]
            },
            "vocational_rehab": {
                "main_question": "Have you participated in a vocational rehabilitation program? Please answer YES or NO.",
                "variations": [
                    "Have you participated in a vocational rehabilitation program? Please answer YES or NO.",
                    "Have you been part of a vocational rehabilitation program? Please answer YES or NO.",
                    "Do you have experience with vocational rehabilitation programs? Please answer YES or NO."
                ],
                "follow_ups": [
                    "Thank you. Next, I'll ask about SSI benefits.",
                    "Got it. I'll ask about SSI benefits next.",
                    "Thanks. Moving on to SSI benefits."
                ],
                "contextual_questions": [
                    "Appreciate that. Ready for the next one?",
                    "Thanks for clarifying. Let's continue.",
                    "Understood. I'll keep this brief."
                ]
            },
            "ssi": {
                "main_question": "Have you received a Supplemental Security Income (SSI) check from the government anytime since 3 months ago? Please answer YES or NO.",
                "variations": [
                    "Have you received a Supplemental Security Income (SSI) check from the government anytime since 3 months ago? Please answer YES or NO.",
                    "Since 3 months ago, have you received any SSI checks from the government? Please answer YES or NO.",
                    "Have you received SSI benefits in the last 3 months? Please answer YES or NO."
                ],
                "follow_ups": [
                    "Thank you. Next, I'll ask about manager information.",
                    "Got it. I'll ask about manager information next.",
                    "Thanks. Moving on to manager information."
                ],
                "contextual_questions": [
                    "Appreciate that. Ready for the next one?",
                    "Thanks for clarifying. Let's continue.",
                    "Understood. I'll keep this brief."
                ]
            },
            "manager_info": {
                "main_question": "If available, please have your hiring manager provide additional information. If your manager is not available, please continue. Please say 'Ready' when prepared to continue.",
                "variations": [
                    "If available, please have your hiring manager provide additional information. If your manager is not available, please continue. Please say 'Ready' when prepared to continue.",
                    "Please have your hiring manager provide additional information if available. If not, please continue. Say 'Ready' when prepared.",
                    "If your hiring manager is available, please have them provide additional information. Otherwise, continue. Say 'Ready' when prepared."
                ],
                "follow_ups": [
                    "Thank you. I'll provide the eligibility result next.",
                    "Got it. I'll provide the eligibility result next.",
                    "Thanks. Moving on to the eligibility result."
                ],
                "contextual_questions": [
                    "Appreciate that. Ready for the result?",
                    "Thanks for clarifying. Let's continue.",
                    "Understood. I'll provide the result now."
                ]
            },
            "eligibility_result": {
                "main_question": "Your employer is not eligible for a tax credit.",
                "variations": [
                    "Your employer is not eligible for a tax credit.",
                    "Based on the information provided, your employer is not eligible for a tax credit.",
                    "I need to inform you that your employer is not eligible for a tax credit."
                ],
                "follow_ups": [
                    "Thank you. Next, I'll ask for employment dates.",
                    "Got it. I'll ask for employment dates next.",
                    "Thanks. Moving on to employment dates."
                ],
                "contextual_questions": [
                    "Appreciate that. Ready for employment dates?",
                    "Thanks for clarifying. Let's continue.",
                    "Understood. I'll ask for employment dates now."
                ]
            },
            "hire_date": {
                "main_question": "Please provide the applicant's Hire Date in MM/DD/YYYY format.",
                "variations": [
                    "Please provide the applicant's Hire Date in MM/DD/YYYY format.",
                    "What is the applicant's Hire Date? Please use MM/DD/YYYY format.",
                    "Could you provide the applicant's Hire Date in MM/DD/YYYY format?"
                ],
                "follow_ups": [
                    "Thank you. Next, I'll ask for the Start Date.",
                    "Got it. I'll ask for the Start Date next.",
                    "Thanks. Moving on to the Start Date."
                ],
                "contextual_questions": [
                    "Appreciate that. Ready for the Start Date?",
                    "Thanks for clarifying. Let's continue.",
                    "Understood. I'll ask for the Start Date now."
                ]
            },
            "start_date": {
                "main_question": "Please provide the applicant's Start Date in MM/DD/YYYY format.",
                "variations": [
                    "Please provide the applicant's Start Date in MM/DD/YYYY format.",
                    "What is the applicant's Start Date? Please use MM/DD/YYYY format.",
                    "Could you provide the applicant's Start Date in MM/DD/YYYY format?"
                ],
                "follow_ups": [
                    "Thank you. I'll provide your confirmation number next.",
                    "Got it. I'll provide your confirmation number next.",
                    "Thanks. Moving on to your confirmation number."
                ],
                "contextual_questions": [
                    "Appreciate that. Ready for your confirmation number?",
                    "Thanks for clarifying. Let's continue.",
                    "Understood. I'll provide your confirmation number now."
                ]
            },
            "confirmation": {
                "main_question": "Your confirmation number is 030F9ADCEN. Would you like to hear that number again?",
                "variations": [
                    "Your confirmation number is 030F9ADCEN. Would you like to hear that number again?",
                    "Your confirmation number is 030F9ADCEN. Should I repeat that number?",
                    "Your confirmation number is 030F9ADCEN. Would you like me to repeat it?"
                ],
                "follow_ups": [
                    "Thank you. That completes our call.",
                    "Perfect—that's everything. Thanks for your time!",
                    "Great, we're all set. Thanks for your time."
                ],
                "contextual_questions": [
                    "Thanks for confirming. We're all set.",
                    "Appreciate your time—that's everything I needed.",
                    "Thank you. I have what I need now."
                ]
            },
            "general": {
                "main_question": "Tell me more about your needs.",
                "variations": [
                    "I'd love to learn more about your situation. Could you tell me more?",
                    "To better understand your needs, could you provide more details?",
                    "That's helpful information. What else should I know about your requirements?",
                    "I'm curious to learn more. Could you elaborate on that?",
                    "To provide the best recommendations, what else can you tell me?"
                ],
                "follow_ups": [
                    "That's very helpful! What other aspects should we discuss?",
                    "Great information! What else would be important to know?",
                    "Perfect! Are there other considerations I should be aware of?",
                    "Thanks! What other details would help me understand your needs?",
                    "Excellent! What else would you like me to know?"
                ],
                "contextual_questions": [
                    "Based on what you've shared, what other factors should we consider?",
                    "That gives me a good picture. What other aspects are important?",
                    "Great context! What other requirements should we discuss?",
                    "That's helpful! What other considerations are important?",
                    "Perfect! What else would help me provide better recommendations?"
                ]
            }
        }
        
        # Conversation flow patterns
        self.conversation_patterns = [
            ["name", "ssn", "address", "cash_assistance", "eligibility_limitation", "other_assistance", "felony", "vocational_rehab", "ssi", "manager_info", "eligibility_result", "hire_date", "start_date", "confirmation"],
            ["name", "address", "cash_assistance", "eligibility_limitation", "other_assistance", "felony", "vocational_rehab", "ssi", "manager_info", "eligibility_result", "hire_date", "start_date", "confirmation"],
            ["name", "cash_assistance", "eligibility_limitation", "other_assistance", "felony", "vocational_rehab", "ssi", "manager_info", "eligibility_result", "hire_date", "start_date", "confirmation"]
        ]
        
        # Natural conversation transitions
        self.transitions = [
            "That's really helpful context!",
            "Thanks for sharing that with me.",
            "That makes perfect sense.",
            "I appreciate you telling me that.",
            "That's very insightful.",
            "That helps me understand your situation better.",
            "Perfect! That gives me a clear picture.",
            "Excellent! That's exactly what I needed to know.",
            "That's really valuable information.",
            "Thanks! That helps me tailor my recommendations."
        ]
        
        # Error handling and fallback responses
        self.fallbacks = {
            "unclear": [
                "I didn't quite catch that. Could you repeat it?",
                "Sorry, I missed that. Can you say it again?",
                "I didn't hear you clearly. Could you repeat that?",
                "That wasn't clear to me. Can you say it again?",
                "I'm having trouble understanding. Could you repeat that?"
            ],
            "out_of_scope": [
                "That's an interesting question, but let me focus on helping you with your business needs. ",
                "I'd love to chat about that, but let me stay focused on understanding your requirements. ",
                "That's a great topic, but let me help you with your current needs first. ",
                "I appreciate your question, but let me focus on what you're looking for. ",
                "That's interesting, but let me help you with your business requirements. "
            ],
            "confirmation": [
                "Did I get that right?",
                "Is that correct?",
                "Let me make sure I understood that correctly.",
                "Can you confirm that's accurate?",
                "Just to be clear, is that right?"
            ]
        }
        
        # Conversation state
        self.conversation_state = {
            "current_topic": None,
            "completed_topics": set(),
            "current_pattern": 0,
            "last_response": None,
            "conversation_start": None,
            "user_engagement": "neutral",  # low, neutral, high
            "conversation_flow": "natural"  # natural, guided, recovery
        }
    
    def start_conversation(self) -> Tuple[str, str]:
        """Start a natural conversation instead of rigid questions."""
        self.conversation_state["conversation_start"] = datetime.now()
        self.conversation_state["current_pattern"] = random.randint(0, len(self.conversation_patterns) - 1)
        
        # Choose a natural opening
        openings = [
            "Hi there! I'm excited to help you find the right solution for your business. To get started, I'd love to understand your situation better.",
            "Hello! I'm here to help you with your business needs. Let me get to know you a bit better so I can provide the best recommendations.",
            "Hi! Thanks for taking the time to chat with me today. I want to understand your business needs so I can help you find the perfect solution.",
            "Hello there! I'm looking forward to helping you today. To give you the best advice, I'd love to learn more about your business.",
            "Hi! I'm here to help you with your business requirements. Let me start by understanding your current situation better."
        ]
        
        opening = random.choice(openings)
        
        # Get the first topic naturally
        first_topic = self.conversation_patterns[self.conversation_state["current_pattern"]][0]
        self.conversation_state["current_topic"] = first_topic
        
        # Create a natural first question
        first_question = self._get_natural_question(first_topic)
        
        return opening + " " + first_question, first_topic
    
    def _get_natural_question(self, topic: str) -> str:
        """Get a natural, conversational question for a topic."""
        topic_data = self.conversation_topics[topic]
        return random.choice(topic_data["variations"])
    
    def process_response(self, user_response: str, current_topic: str) -> Tuple[str, str, str]:
        """
        Process user response and generate next conversational turn.
        Returns: (response_text, next_topic, conversation_state)
        """
        # Update conversation state
        self.conversation_state["last_response"] = user_response
        self.conversation_state["completed_topics"].add(current_topic)
        
        # Analyze user engagement
        self._analyze_engagement(user_response)
        
        # Generate natural response
        response = self._generate_natural_response(user_response, current_topic)
        
        # Determine next topic
        next_topic = self._get_next_topic(current_topic)
        
        # Update state
        self.conversation_state["current_topic"] = next_topic
        
        return response, next_topic, self._get_conversation_summary()
    
    def _analyze_engagement(self, user_response: str):
        """Analyze user engagement level from their response."""
        response_length = len(user_response.split())
        
        if response_length < 3:
            self.conversation_state["user_engagement"] = "low"
        elif response_length > 10:
            self.conversation_state["user_engagement"] = "high"
        else:
            self.conversation_state["user_engagement"] = "neutral"
    
    def _generate_natural_response(self, user_response: str, current_topic: str) -> str:
        """Generate a natural, conversational response."""
        # Add a natural transition
        transition = random.choice(self.transitions)
        
        # Get contextual follow-up based on engagement
        if self.conversation_state["user_engagement"] == "high":
            # User is engaged, ask deeper questions
            follow_up = self._get_contextual_followup(current_topic)
        else:
            # User is less engaged, keep it simple
            follow_up = self._get_simple_followup(current_topic)
        
        return transition + " " + follow_up
    
    def _get_contextual_followup(self, current_topic: str) -> str:
        """Get a contextual follow-up question for engaged users."""
        topic_data = self.conversation_topics[current_topic]
        return random.choice(topic_data["contextual_questions"])
    
    def _get_simple_followup(self, current_topic: str) -> str:
        """Get a simple follow-up question for less engaged users."""
        topic_data = self.conversation_topics[current_topic]
        return random.choice(topic_data["follow_ups"])
    
    def _get_next_topic(self, current_topic: str) -> str:
        """Get the next topic in the conversation flow."""
        pattern = self.conversation_patterns[self.conversation_state["current_pattern"]]
        
        try:
            current_index = pattern.index(current_topic)
            next_index = current_index + 1
            
            if next_index < len(pattern):
                return pattern[next_index]
            else:
                # Conversation complete, start over or end
                return "conversation_complete"
        except ValueError:
            # Topic not in pattern, get next available
            for topic in pattern:
                if topic not in self.conversation_state["completed_topics"]:
                    return topic
        
        return "conversation_complete"
    
    def handle_error(self, error_type: str, context: str = "") -> str:
        """Handle errors and provide natural fallback responses."""
        if error_type == "unclear":
            return random.choice(self.fallbacks["unclear"])
        elif error_type == "out_of_scope":
            base = random.choice(self.fallbacks["out_of_scope"])
            return base + self._get_natural_question(self.conversation_state["current_topic"])
        elif error_type == "confirmation":
            return random.choice(self.fallbacks["confirmation"])
        else:
            return "I'm having trouble understanding. Let me ask that again in a different way."
    
    def _get_conversation_summary(self) -> str:
        """Get a summary of the conversation state."""
        return json.dumps({
            "current_topic": self.conversation_state["current_topic"],
            "completed_topics": list(self.conversation_state["completed_topics"]),
            "user_engagement": self.conversation_state["user_engagement"],
            "conversation_flow": self.conversation_state["conversation_flow"],
            "duration": (datetime.now() - self.conversation_state["conversation_start"]).seconds if self.conversation_state["conversation_start"] else 0
        })
    
    def is_conversation_complete(self) -> bool:
        """Check if the conversation has covered all topics."""
        pattern = self.conversation_patterns[self.conversation_state["current_pattern"]]
        return len(self.conversation_state["completed_topics"]) >= len(pattern)
    
    def get_conversation_progress(self) -> float:
        """Get conversation progress as a percentage."""
        pattern = self.conversation_patterns[self.conversation_state["current_pattern"]]
        return len(self.conversation_state["completed_topics"]) / len(pattern) * 100

# Example usage:
# engine = ConversationEngine()
# opening, first_topic = engine.start_conversation()
# response, next_topic, state = engine.process_response("We have about 50 employees", "company_size")
