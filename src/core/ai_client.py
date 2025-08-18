"""
OpenAI API client with safety filters for heyBuddy
Supports both English and German language modes
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from core.config import settings
from core.german_ai import GermanContentFilter, GermanAIPersona, GermanSafetyResponse

logger = logging.getLogger(__name__)


class SafetyFilter:
    """Content moderation and safety filtering"""
    
    def __init__(self, client: AsyncOpenAI):
        self.client = client
        
    async def moderate_content(self, content: str) -> Dict[str, Any]:
        """Check content using OpenAI Moderation API"""
        try:
            response = await self.client.moderations.create(input=content)
            result = response.results[0]
            
            return {
                "flagged": result.flagged,
                "categories": dict(result.categories),
                "category_scores": dict(result.category_scores),
                "safe": not result.flagged
            }
        except Exception as e:
            logger.error(f"Moderation API error: {e}")
            # Fail safe: if moderation fails, assume content is unsafe
            return {
                "flagged": True,
                "categories": {"error": True},
                "category_scores": {"error": 1.0},
                "safe": False,
                "error": str(e)
            }
    
    def apply_age_appropriate_filter(self, content: str, age: Optional[int] = None) -> bool:
        """Apply age-appropriate content filtering"""
        if not age:
            age = 8  # Default safe age
            
        # Simple keyword filtering for demonstration
        # In production, this would be more sophisticated
        inappropriate_keywords = [
            "violence", "scary", "death", "kill", "blood", "war",
            "adult", "mature", "inappropriate"
        ]
        
        content_lower = content.lower()
        for keyword in inappropriate_keywords:
            if keyword in content_lower:
                logger.warning(f"Age filter blocked content containing: {keyword}")
                return False
                
        return True


class AIPersona:
    """AI personality configuration for different age groups and contexts"""
    
    @staticmethod
    def get_system_prompt(age: Optional[int] = None, persona: str = "friendly") -> str:
        """Generate system prompt based on age and persona"""
        
        base_prompt = """You are heyBuddy, a friendly AI companion designed to help children learn and grow. You are:

- Kind, patient, and encouraging
- Focused on emotional support and learning
- Always positive and constructive
- Appropriate for children
- Helpful with daily routines and goals

Remember:
- Keep responses short and age-appropriate
- Use simple, clear language
- Be encouraging and supportive
- Never discuss inappropriate topics
- Focus on positive learning experiences
"""
        
        if age and age <= 6:
            return base_prompt + """
Additional guidelines for young children:
- Use very simple words and short sentences
- Be extra gentle and reassuring
- Include fun elements like counting or simple games
- Speak like a caring friend, not a teacher
"""
        elif age and age <= 12:
            return base_prompt + """
Additional guidelines for school-age children:
- Use slightly more complex vocabulary
- Help with homework encouragement
- Discuss emotions and friendship
- Support goal-setting and achievement
"""
        else:
            return base_prompt


class AIClient:
    """Main AI client with safety and conversation management"""
    
    def __init__(self, language: str = "en"):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.safety_filter = SafetyFilter(self.client)
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        self.language = language
        self.german_filter = GermanContentFilter() if language == "de" else None
        
    async def initialize(self) -> bool:
        """Initialize and test the AI client"""
        try:
            # Test the connection with a simple moderation call
            test_result = await self.safety_filter.moderate_content("Hello, this is a test.")
            if "error" not in test_result:
                logger.info("AI client initialized successfully")
                return True
            else:
                logger.error("AI client test failed")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            return False
    
    async def process_conversation(
        self, 
        user_input: str, 
        user_id: str,
        age: Optional[int] = None,
        persona: str = "friendly"
    ) -> Dict[str, Any]:
        """Process a conversation with safety filtering"""
        
        # Step 1: Moderate user input
        input_moderation = await self.safety_filter.moderate_content(user_input)
        if not input_moderation["safe"]:
            logger.warning(f"User input blocked by moderation: {user_input[:50]}")
            error_message = (GermanSafetyResponse.get_response("inappropriate") 
                           if self.language == "de" 
                           else "I can't help with that. Let's talk about something else!")
            return {
                "success": False,
                "error": "inappropriate_input",
                "message": error_message
            }
        
        # Step 2: Apply German content filtering if language is German
        if self.language == "de" and self.german_filter:
            german_check = self.german_filter.check_content_appropriateness(user_input, age)
            if not german_check["safe"]:
                logger.warning(f"German filter blocked content: {german_check['flagged_words']}")
                return {
                    "success": False,
                    "error": "german_inappropriate",
                    "message": GermanSafetyResponse.get_response("inappropriate"),
                    "german_analysis": german_check
                }
        
        # Step 3: Apply age-appropriate filtering (English legacy)
        if self.language == "en" and not self.safety_filter.apply_age_appropriate_filter(user_input, age):
            return {
                "success": False,
                "error": "age_inappropriate",
                "message": "Let's talk about something more fun and appropriate!"
            }
        
        # Step 4: Check for emotional support needs (German)
        emotional_support_data = None
        if self.language == "de" and self.german_filter:
            german_check = self.german_filter.check_content_appropriateness(user_input, age)
            if german_check["emotional_support_needed"]:
                emotional_support_data = german_check
                logger.info(f"Emotional support detected: {german_check['emotional_keywords']}")
        
        # Step 5: Generate AI response
        try:
            response = await self._generate_response(user_input, user_id, age, persona, emotional_support_data)
            
            # Step 6: Moderate AI response
            output_moderation = await self.safety_filter.moderate_content(response)
            if not output_moderation["safe"]:
                logger.warning(f"AI response blocked by moderation: {response[:50]}")
                error_message = (GermanSafetyResponse.get_response("error") 
                               if self.language == "de" 
                               else "Let me think of a better way to help you with that!")
                return {
                    "success": False,
                    "error": "inappropriate_output",
                    "message": error_message
                }
            
            # Step 7: Apply age filter to response (English legacy)
            if self.language == "en" and not self.safety_filter.apply_age_appropriate_filter(response, age):
                return {
                    "success": False,
                    "error": "age_inappropriate_output",
                    "message": "Let me help you with something more suitable!"
                }
            
            # Step 8: Store conversation (truncated for memory management)
            self._store_conversation(user_id, user_input, response)
            
            result = {
                "success": True,
                "response": response,
                "input_moderation": input_moderation,
                "output_moderation": output_moderation,
                "language": self.language
            }
            
            # Add emotional support info if detected
            if emotional_support_data:
                result["emotional_support"] = emotional_support_data
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            return {
                "success": False,
                "error": "processing_error",
                "message": "I'm having trouble thinking right now. Can you try again?"
            }
    
    async def _generate_response(
        self, 
        user_input: str, 
        user_id: str,
        age: Optional[int],
        persona: str,
        emotional_support_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate AI response using OpenAI API"""
        
        # Get conversation history
        history = self.conversation_history.get(user_id, [])
        
        # Build system prompt based on language
        if self.language == "de":
            if emotional_support_data and emotional_support_data["emotional_support_needed"]:
                # Use emotional support prompt for German
                system_prompt = GermanAIPersona.get_emotional_support_prompt(
                    emotional_support_data["emotional_keywords"]
                )
            else:
                system_prompt = GermanAIPersona.get_german_system_prompt(age, persona)
        else:
            system_prompt = AIPersona.get_system_prompt(age, persona)
        
        # Build messages for API call
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add recent conversation history (limit to prevent token overflow)
        for entry in history[-5:]:  # Last 5 exchanges
            messages.append({"role": "user", "content": entry["user"]})
            messages.append({"role": "assistant", "content": entry["assistant"]})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        # Call OpenAI API
        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=settings.openai_max_tokens,
            temperature=settings.openai_temperature,
            presence_penalty=0.1,
            frequency_penalty=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    def _store_conversation(self, user_id: str, user_input: str, ai_response: str):
        """Store conversation in memory (with size limits)"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "user": user_input,
            "assistant": ai_response
        })
        
        # Limit conversation history size
        max_history = settings.max_conversation_length
        if len(self.conversation_history[user_id]) > max_history:
            self.conversation_history[user_id] = self.conversation_history[user_id][-max_history:]
    
    async def generate_story(self, theme: str, age: Optional[int] = None) -> Dict[str, Any]:
        """Generate a safe, age-appropriate story"""
        
        if self.language == "de":
            # For German, use direct API call with storytelling prompt
            try:
                system_prompt = GermanAIPersona.get_storytelling_prompt(theme, age)
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Erzähle eine Geschichte über {theme}"}
                ]
                
                response = await self.client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,
                    max_tokens=200,  # Longer for stories
                    temperature=0.8,  # More creative for stories
                    presence_penalty=0.1,
                    frequency_penalty=0.1
                )
                
                story = response.choices[0].message.content.strip()
                
                # Moderate the generated story
                moderation = await self.safety_filter.moderate_content(story)
                if not moderation["safe"]:
                    return {
                        "success": False,
                        "error": "inappropriate_story",
                        "message": "Entschuldigung, ich denke mir eine andere Geschichte aus."
                    }
                
                return {
                    "success": True,
                    "response": story,
                    "language": "de"
                }
                
            except Exception as e:
                logger.error(f"Error generating German story: {e}")
                return {
                    "success": False,
                    "error": "story_generation_error",
                    "message": "Entschuldigung, ich kann gerade keine Geschichte erzählen. Versuche es später nochmal."
                }
        else:
            # English story generation
            prompt = f"Tell a short, wholesome story about {theme}. "
            if age:
                if age <= 6:
                    prompt += "Use very simple words for a young child. Keep it under 100 words."
                elif age <= 12:
                    prompt += "Make it appropriate for a school-age child. Keep it under 150 words."
            else:
                prompt += "Keep it appropriate for children and under 150 words."
            
            return await self.process_conversation(prompt, "story_generator", age, "storyteller")
    
    async def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of recent conversation for parental oversight"""
        history = self.conversation_history.get(user_id, [])
        
        if not history:
            return {"summary": "No recent conversations", "topics": [], "message_count": 0}
        
        # Extract topics and create summary
        recent_topics = []
        message_count = len(history)
        
        # Simple topic extraction (in production, this could be more sophisticated)
        for entry in history[-3:]:  # Last 3 exchanges
            user_msg = entry["user"].lower()
            if any(keyword in user_msg for keyword in ["story", "tell me"]):
                recent_topics.append("storytelling")
            elif any(keyword in user_msg for keyword in ["scared", "afraid", "worry"]):
                recent_topics.append("emotions/fears")
            elif any(keyword in user_msg for keyword in ["homework", "school"]):
                recent_topics.append("school")
            elif any(keyword in user_msg for keyword in ["friend", "play"]):
                recent_topics.append("friendship/play")
            else:
                recent_topics.append("general conversation")
        
        return {
            "summary": f"Recent conversation covered {len(set(recent_topics))} main topics",
            "topics": list(set(recent_topics)),
            "message_count": message_count,
            "last_interaction": "recent" if history else "none"
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.close()
        logger.info("AI client cleaned up")