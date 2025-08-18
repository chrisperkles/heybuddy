"""
API routes for heyBuddy companion app
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import logging
from typing import Optional, Dict, Any
import asyncio
import io

from core.ai_client import AIClient
from core.safety import SafetyManager
from core.audio import AudioManager
from core.config import settings

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class ConversationRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    user_id: str = Field(..., min_length=1, max_length=50)
    age: Optional[int] = Field(None, ge=3, le=18)
    persona: str = Field(default="friendly")

class ConversationResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    safety_info: Optional[Dict[str, Any]] = None
    needs_adult_attention: bool = False

class VoiceConversationRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)
    age: Optional[int] = Field(None, ge=3, le=18)
    persona: str = Field(default="friendly")
    duration: float = Field(default=5.0, ge=1.0, le=10.0)

class StoryRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=3, le=18)
    user_id: str = Field(..., min_length=1, max_length=50)

class UserSessionRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)


def create_conversation_router(audio_manager: AudioManager, database=None, websocket_manager=None) -> APIRouter:
    """Create conversation router with dependencies"""
    router = APIRouter(prefix="/conversation", tags=["conversation"])
    
    # Initialize AI client and safety manager with language setting
    ai_client = AIClient(language=settings.language)
    safety_manager = SafetyManager()
    
    @router.on_event("startup")
    async def startup():
        """Initialize AI client on startup"""
        success = await ai_client.initialize()
        if not success:
            logger.error("Failed to initialize AI client")
    
    @router.on_event("shutdown")
    async def shutdown():
        """Cleanup on shutdown"""
        await ai_client.cleanup()
    
    @router.post("/text", response_model=ConversationResponse)
    async def text_conversation(request: ConversationRequest):
        """Process text-based conversation"""
        try:
            logger.info(f"Text conversation request from user {request.user_id}")
            
            # Safety validation
            safety_result = await safety_manager.validate_interaction(
                user_id=request.user_id,
                content=request.message,
                age=request.age,
                is_user_input=True
            )
            
            if not safety_result["safe"]:
                # Handle different types of safety issues
                if safety_result.get("crisis"):
                    return ConversationResponse(
                        success=False,
                        error="crisis_detected",
                        response=safety_result["response"],
                        needs_adult_attention=True,
                        safety_info=safety_result
                    )
                
                return ConversationResponse(
                    success=False,
                    error=safety_result.get("reason", "safety_check_failed"),
                    response=safety_result.get("suggestion", "Let's talk about something else!"),
                    safety_info=safety_result
                )
            
            # Process with AI
            ai_result = await ai_client.process_conversation(
                user_input=request.message,
                user_id=request.user_id,
                age=request.age,
                persona=request.persona
            )
            
            if not ai_result["success"]:
                return ConversationResponse(
                    success=False,
                    error=ai_result["error"],
                    response=ai_result["message"]
                )
            
            # Check if emotional support is needed
            needs_attention = safety_result.get("needs_emotional_support", False)
            
            # Use support response if provided
            final_response = ai_result["response"]
            if safety_result.get("support_response"):
                final_response = safety_result["support_response"] + " " + final_response
            
            # Send real-time notification to parents if needed
            if websocket_manager and needs_attention:
                await websocket_manager.notifier.notify_emotional_support(
                    user_id=request.user_id,
                    family_id="default",  # In production, this would be user's family_id
                    details={
                        "emotional_keywords": safety_result.get("emotional_keywords", []),
                        "message": "Child expressed emotional needs",
                        "support_provided": True
                    }
                )
            
            # Store conversation in database if available
            if database:
                try:
                    database.store_conversation(
                        user_id=request.user_id,
                        user_message=request.message,
                        ai_response=final_response,
                        metadata={
                            "type": "text",
                            "persona": request.persona,
                            "emotional_support": needs_attention,
                            "category": "emotional_support" if needs_attention else "general"
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to store conversation: {e}")
            
            return ConversationResponse(
                success=True,
                response=final_response,
                needs_adult_attention=needs_attention,
                safety_info={
                    "input_safe": True,
                    "output_safe": True,
                    "emotional_support": safety_result.get("needs_emotional_support", False)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in text conversation: {e}")
            return ConversationResponse(
                success=False,
                error="processing_error",
                response="I'm having trouble thinking right now. Can you try again?"
            )
    
    @router.post("/voice", response_model=ConversationResponse)
    async def voice_conversation(request: VoiceConversationRequest):
        """Process voice-based conversation"""
        try:
            logger.info(f"Voice conversation request from user {request.user_id}")
            
            # Record audio
            audio_data = await audio_manager.record_audio(duration=request.duration)
            
            # Convert speech to text (placeholder - would use Whisper API)
            # For now, simulate with a test message
            user_text = "Hello, this is a test voice message"
            logger.info(f"Simulated speech-to-text: {user_text}")
            
            # Process as text conversation
            text_request = ConversationRequest(
                message=user_text,
                user_id=request.user_id,
                age=request.age,
                persona=request.persona
            )
            
            conversation_result = await text_conversation(text_request)
            
            if conversation_result.success:
                # Convert response to speech (placeholder - would use OpenAI TTS)
                response_audio = await _text_to_speech(conversation_result.response)
                
                # Play audio response
                await audio_manager.play_audio(response_audio)
                
                logger.info("Voice conversation completed successfully")
            
            return conversation_result
            
        except Exception as e:
            logger.error(f"Error in voice conversation: {e}")
            return ConversationResponse(
                success=False,
                error="voice_processing_error",
                response="I'm having trouble hearing you. Can you try again?"
            )
    
    @router.post("/story", response_model=ConversationResponse)
    async def generate_story(request: StoryRequest):
        """Generate a story for the user"""
        try:
            logger.info(f"Story request for theme '{request.theme}' from user {request.user_id}")
            
            # Safety check on story theme
            safety_result = await safety_manager.validate_interaction(
                user_id=request.user_id,
                content=f"story about {request.theme}",
                age=request.age,
                is_user_input=True
            )
            
            if not safety_result["safe"]:
                return ConversationResponse(
                    success=False,
                    error="inappropriate_theme",
                    response="Let's choose a different story theme that's more fun!"
                )
            
            # Generate story
            story_result = await ai_client.generate_story(request.theme, request.age)
            
            if not story_result["success"]:
                return ConversationResponse(
                    success=False,
                    error=story_result["error"],
                    response="I'm having trouble thinking of a story right now. Can you suggest a different theme?"
                )
            
            return ConversationResponse(
                success=True,
                response=story_result["response"],
                safety_info={"story_theme_safe": True}
            )
            
        except Exception as e:
            logger.error(f"Error generating story: {e}")
            return ConversationResponse(
                success=False,
                error="story_generation_error",
                response="I'm having trouble making up a story right now. Can you try again later?"
            )
    
    @router.get("/summary/{user_id}")
    async def get_conversation_summary(user_id: str):
        """Get conversation summary for parental oversight"""
        try:
            # Get AI conversation summary
            ai_summary = await ai_client.get_conversation_summary(user_id)
            
            # Get safety summary
            safety_summary = safety_manager.get_parental_summary(user_id)
            
            return {
                "user_id": user_id,
                "conversation_summary": ai_summary,
                "safety_summary": safety_summary,
                "timestamp": "recent"
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            raise HTTPException(status_code=500, detail="Failed to get conversation summary")
    
    @router.post("/session/end")
    async def end_user_session(request: UserSessionRequest):
        """End user conversation session"""
        try:
            result = safety_manager.end_user_session(request.user_id)
            return {
                "success": True,
                "session_ended": True,
                "summary": result
            }
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            raise HTTPException(status_code=500, detail="Failed to end session")
    
    return router


async def _text_to_speech(text: str) -> bytes:
    """Convert text to speech (placeholder implementation)"""
    # This would use OpenAI TTS API in production
    # For now, return silence as placeholder
    
    # Generate 2 seconds of silence as WAV
    import wave
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        # 2 seconds of silence
        silence = b'\x00' * (16000 * 2 * 2)
        wav_file.writeframes(silence)
    
    buffer.seek(0)
    logger.info(f"Generated TTS audio for text: {text[:50]}...")
    return buffer.getvalue()


async def _speech_to_text(audio_data: bytes) -> str:
    """Convert speech to text (placeholder implementation)"""
    # This would use OpenAI Whisper API in production
    # For now, return a placeholder response
    logger.info("Processed speech-to-text (simulated)")
    return "This is a simulated speech recognition result"