"""
Safety and content moderation utilities for heyBuddy
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class ContentValidator:
    """Validates content for safety and appropriateness"""
    
    # Age-appropriate content guidelines
    SAFE_TOPICS = {
        "young": [  # Ages 4-6
            "animals", "colors", "counting", "shapes", "family", "friends",
            "playground", "toys", "books", "songs", "food", "weather"
        ],
        "school": [  # Ages 7-12
            "school", "homework", "sports", "hobbies", "science", "nature",
            "art", "music", "travel", "cooking", "games", "friendship"
        ]
    }
    
    BLOCKED_TOPICS = [
        "violence", "weapons", "death", "injury", "blood", "fighting",
        "scary", "horror", "nightmare", "monster", "ghost", "demon",
        "adult themes", "inappropriate", "mature content", "dating",
        "money", "politics", "religion", "drugs", "alcohol", "smoking"
    ]
    
    EMOTIONAL_SUPPORT_KEYWORDS = [
        "sad", "scared", "afraid", "worried", "angry", "upset", "lonely",
        "frustrated", "confused", "nervous", "anxious", "mad"
    ]
    
    @classmethod
    def validate_content(cls, content: str, age: Optional[int] = None) -> Dict[str, Any]:
        """Validate content for safety and age-appropriateness"""
        content_lower = content.lower()
        
        # Check for blocked topics
        blocked_found = []
        for blocked in cls.BLOCKED_TOPICS:
            if blocked in content_lower:
                blocked_found.append(blocked)
        
        if blocked_found:
            return {
                "safe": False,
                "reason": "blocked_topics",
                "blocked_items": blocked_found,
                "suggestion": "Let's talk about something more fun!"
            }
        
        # Check for emotional distress
        emotional_keywords = []
        for keyword in cls.EMOTIONAL_SUPPORT_KEYWORDS:
            if keyword in content_lower:
                emotional_keywords.append(keyword)
        
        # Content length check
        if len(content) > 500:
            return {
                "safe": False,
                "reason": "too_long",
                "suggestion": "Can you tell me that in fewer words?"
            }
        
        return {
            "safe": True,
            "emotional_keywords": emotional_keywords,
            "needs_support": len(emotional_keywords) > 0,
            "age_appropriate": cls._check_age_appropriate(content_lower, age)
        }
    
    @classmethod
    def _check_age_appropriate(cls, content: str, age: Optional[int]) -> bool:
        """Check if content is appropriate for the given age"""
        if not age:
            return True  # Default to permissive if age unknown
        
        # Very young children (4-6) - strict filtering
        if age <= 6:
            complex_words = ["because", "however", "therefore", "although", "consequently"]
            if any(word in content for word in complex_words):
                return False
        
        # School age (7-12) - moderate filtering
        elif age <= 12:
            adult_concepts = ["mortgage", "taxes", "politics", "economics", "philosophy"]
            if any(concept in content for concept in adult_concepts):
                return False
        
        return True


class ConversationMonitor:
    """Monitors conversation patterns for safety"""
    
    def __init__(self):
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.max_session_duration = timedelta(hours=2)
        self.max_messages_per_session = 50
    
    def start_session(self, user_id: str, age: Optional[int] = None) -> Dict[str, Any]:
        """Start a new conversation session"""
        self.user_sessions[user_id] = {
            "start_time": datetime.now(),
            "message_count": 0,
            "age": age,
            "topics": [],
            "emotional_flags": [],
            "safety_warnings": 0
        }
        
        logger.info(f"Started conversation session for user {user_id}")
        return {"session_started": True, "session_id": user_id}
    
    def log_message(self, user_id: str, content: str, is_user: bool = True) -> Dict[str, Any]:
        """Log a message and check session limits"""
        if user_id not in self.user_sessions:
            self.start_session(user_id)
        
        session = self.user_sessions[user_id]
        session["message_count"] += 1
        
        # Check session duration
        session_duration = datetime.now() - session["start_time"]
        if session_duration > self.max_session_duration:
            return {
                "continue": False,
                "reason": "session_timeout",
                "message": "You've been chatting for a while! Time for a break."
            }
        
        # Check message count
        if session["message_count"] > self.max_messages_per_session:
            return {
                "continue": False,
                "reason": "message_limit",
                "message": "We've talked a lot today! Let's continue later."
            }
        
        # Validate content if it's from user
        if is_user:
            validation = ContentValidator.validate_content(content, session["age"])
            if not validation["safe"]:
                session["safety_warnings"] += 1
                
                if session["safety_warnings"] >= 3:
                    return {
                        "continue": False,
                        "reason": "safety_warnings",
                        "message": "Let's talk about something else. How about we play a game?"
                    }
                
                return {
                    "continue": True,
                    "warning": True,
                    "validation": validation
                }
            
            # Track emotional support needs
            if validation.get("needs_support"):
                session["emotional_flags"].extend(validation["emotional_keywords"])
        
        return {"continue": True, "session_healthy": True}
    
    def get_session_summary(self, user_id: str) -> Dict[str, Any]:
        """Get session summary for parental oversight"""
        if user_id not in self.user_sessions:
            return {"no_session": True}
        
        session = self.user_sessions[user_id]
        duration = datetime.now() - session["start_time"]
        
        return {
            "duration_minutes": int(duration.total_seconds() / 60),
            "message_count": session["message_count"],
            "safety_warnings": session["safety_warnings"],
            "emotional_support_needed": len(session["emotional_flags"]) > 0,
            "emotional_keywords": list(set(session["emotional_flags"])),
            "session_healthy": session["safety_warnings"] < 3
        }
    
    def end_session(self, user_id: str) -> Dict[str, Any]:
        """End conversation session"""
        if user_id in self.user_sessions:
            summary = self.get_session_summary(user_id)
            del self.user_sessions[user_id]
            logger.info(f"Ended conversation session for user {user_id}")
            return {"session_ended": True, "summary": summary}
        return {"no_session": True}


class EmergencyHandler:
    """Handles emergency situations and crisis detection"""
    
    CRISIS_KEYWORDS = [
        "hurt myself", "want to die", "kill myself", "hate myself",
        "nobody loves me", "everyone hates me", "want to disappear",
        "hurt someone", "hurt others", "violence", "weapon"
    ]
    
    DISTRESS_KEYWORDS = [
        "very sad", "really scared", "can't stop crying", "having nightmares",
        "can't sleep", "don't want to eat", "stomach hurts", "head hurts"
    ]
    
    @classmethod
    def check_crisis_indicators(cls, content: str) -> Dict[str, Any]:
        """Check for crisis or emergency indicators"""
        content_lower = content.lower()
        
        crisis_found = []
        distress_found = []
        
        for keyword in cls.CRISIS_KEYWORDS:
            if keyword in content_lower:
                crisis_found.append(keyword)
        
        for keyword in cls.DISTRESS_KEYWORDS:
            if keyword in content_lower:
                distress_found.append(keyword)
        
        if crisis_found:
            logger.critical(f"CRISIS INDICATORS DETECTED: {crisis_found}")
            return {
                "crisis_level": "HIGH",
                "immediate_action": True,
                "indicators": crisis_found,
                "response": "I'm worried about you. Let's get an adult to help right away."
            }
        
        if distress_found:
            logger.warning(f"Distress indicators detected: {distress_found}")
            return {
                "crisis_level": "MEDIUM",
                "immediate_action": False,
                "indicators": distress_found,
                "response": "I can hear that you're having a hard time. Let's talk about it, and maybe we should get a grown-up to help."
            }
        
        return {"crisis_level": "NONE", "immediate_action": False}
    
    @classmethod
    def generate_support_response(cls, emotional_keywords: List[str]) -> str:
        """Generate supportive response for emotional situations"""
        if not emotional_keywords:
            return "I'm here to listen and help you feel better."
        
        primary_emotion = emotional_keywords[0]
        
        responses = {
            "sad": "It's okay to feel sad sometimes. Can you tell me what's making you feel this way?",
            "scared": "Feeling scared is normal. You're brave for talking about it. What's making you feel scared?",
            "afraid": "It's okay to be afraid. Everyone feels afraid sometimes. What can we do to help you feel safer?",
            "worried": "When we worry, it means we care. What are you worried about? Maybe we can figure it out together.",
            "angry": "It's okay to feel angry, but let's find a good way to handle those feelings. What made you angry?",
            "upset": "I can see you're upset. Take a deep breath with me. What happened?",
            "lonely": "Feeling lonely is hard. But you're not alone - I'm here with you. Tell me more about how you're feeling.",
            "frustrated": "Frustration happens when things don't go the way we want. What's frustrating you right now?"
        }
        
        return responses.get(primary_emotion, "I can hear that you're having some big feelings. That's okay - all feelings are okay. Tell me more about it.")


class SafetyManager:
    """Main safety management coordinator"""
    
    def __init__(self):
        self.conversation_monitor = ConversationMonitor()
        self.active_sessions: Dict[str, bool] = {}
    
    async def validate_interaction(
        self, 
        user_id: str, 
        content: str, 
        age: Optional[int] = None,
        is_user_input: bool = True
    ) -> Dict[str, Any]:
        """Comprehensive safety validation for interactions"""
        
        # Start session if needed
        if user_id not in self.active_sessions:
            self.conversation_monitor.start_session(user_id, age)
            self.active_sessions[user_id] = True
        
        # Check for crisis indicators
        crisis_check = EmergencyHandler.check_crisis_indicators(content)
        if crisis_check["immediate_action"]:
            return {
                "safe": False,
                "crisis": True,
                "level": "HIGH",
                "response": crisis_check["response"],
                "action_required": "IMMEDIATE_ADULT_INTERVENTION"
            }
        
        # Validate content
        validation = ContentValidator.validate_content(content, age)
        if not validation["safe"]:
            return {
                "safe": False,
                "reason": validation["reason"],
                "suggestion": validation["suggestion"]
            }
        
        # Log message and check session limits
        session_check = self.conversation_monitor.log_message(user_id, content, is_user_input)
        if not session_check["continue"]:
            return {
                "safe": False,
                "session_limit": True,
                "reason": session_check["reason"],
                "message": session_check["message"]
            }
        
        # Handle emotional support needs
        support_response = None
        if validation.get("needs_support"):
            support_response = EmergencyHandler.generate_support_response(
                validation["emotional_keywords"]
            )
        
        return {
            "safe": True,
            "validation": validation,
            "crisis_check": crisis_check,
            "session_status": session_check,
            "support_response": support_response,
            "needs_emotional_support": validation.get("needs_support", False)
        }
    
    def get_parental_summary(self, user_id: str) -> Dict[str, Any]:
        """Get safety summary for parental oversight"""
        return self.conversation_monitor.get_session_summary(user_id)
    
    def end_user_session(self, user_id: str) -> Dict[str, Any]:
        """End user session"""
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
        return self.conversation_monitor.end_session(user_id)