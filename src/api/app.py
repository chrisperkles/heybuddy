"""
FastAPI application factory for heyBuddy companion app
"""
from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import logging
from typing import Optional

from core.config import settings
from core.audio import AudioManager
from api.routes import create_conversation_router
from api.websocket import WebSocketManager


logger = logging.getLogger(__name__)
security = HTTPBearer()


def create_app(audio_manager: AudioManager, database=None) -> FastAPI:
    """Create FastAPI application instance"""
    
    app = FastAPI(
        title="heyBuddy Companion API",
        description="REST API for heyBuddy AI Companion parental controls and monitoring",
        version=settings.version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.local"]
    )
    
    # CORS middleware for local network access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Initialize WebSocket manager
    websocket_manager = WebSocketManager()
    
    # Store managers in app state
    app.state.audio_manager = audio_manager
    app.state.database = database
    app.state.websocket_manager = websocket_manager
    
    # Include conversation routes
    conversation_router = create_conversation_router(audio_manager, database, websocket_manager)
    app.include_router(conversation_router)
    
    # WebSocket endpoint for real-time updates
    @app.websocket("/ws/{family_id}")
    async def websocket_endpoint(websocket: WebSocket, family_id: str = "default"):
        await websocket_manager.websocket_endpoint(websocket, family_id)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring"""
        try:
            audio_ok = await audio_manager.is_device_available()
            return {
                "status": "healthy" if audio_ok else "degraded",
                "version": settings.version,
                "audio_device": "available" if audio_ok else "unavailable",
                "environment": settings.environment
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail="Service unhealthy")
    
    # Basic status endpoint
    @app.get("/status")
    async def get_status():
        """Get current system status"""
        return {
            "app_name": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "audio_device_type": settings.audio_device
        }
    
    # Audio test endpoint
    @app.post("/audio/test")
    async def test_audio():
        """Test audio recording and playback"""
        try:
            logger.info("Testing audio system...")
            
            # Record a short audio sample
            audio_data = await audio_manager.record_audio(duration=2.0)
            
            # Play it back
            await audio_manager.play_audio(audio_data)
            
            return {
                "status": "success",
                "message": "Audio test completed successfully",
                "audio_size": len(audio_data)
            }
        except Exception as e:
            logger.error(f"Audio test failed: {e}")
            raise HTTPException(status_code=500, detail=f"Audio test failed: {str(e)}")
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": f"Welcome to {settings.app_name} API",
            "version": settings.version,
            "docs": "/docs" if settings.debug else "Documentation disabled in production",
            "endpoints": {
                "health": "/health",
                "status": "/status", 
                "audio_test": "/audio/test",
                "conversation": "/conversation/text",
                "voice": "/conversation/voice", 
                "story": "/conversation/story",
                "websocket": "/ws/{family_id}",
                "dashboard": "http://localhost:3000"
            }
        }
    
    return app