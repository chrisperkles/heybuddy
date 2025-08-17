"""
WebSocket support for real-time updates to parental dashboard
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.parent_connections: Dict[str, List[str]] = {}  # family_id -> connection_ids
        
    async def connect(self, websocket: WebSocket, connection_id: str, family_id: Optional[str] = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if family_id:
            if family_id not in self.parent_connections:
                self.parent_connections[family_id] = []
            self.parent_connections[family_id].append(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} (family: {family_id})")
        
        # Send initial connection confirmation
        await self.send_personal_message({
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
    
    def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
        # Remove from family connections
        for family_id, connections in self.parent_connections.items():
            if connection_id in connections:
                connections.remove(connection_id)
                if not connections:
                    del self.parent_connections[family_id]
                break
                
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def send_to_family(self, message: Dict[str, Any], family_id: str):
        """Send message to all connections for a family"""
        if family_id in self.parent_connections:
            disconnected = []
            for connection_id in self.parent_connections[family_id]:
                try:
                    websocket = self.active_connections[connection_id]
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending to family {family_id}, connection {connection_id}: {e}")
                    disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for conn_id in disconnected:
                self.disconnect(conn_id)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all active connections"""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for conn_id in disconnected:
            self.disconnect(conn_id)


class RealtimeNotifier:
    """Handles real-time notifications for parental dashboard"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        
    async def notify_conversation_started(self, user_id: str, family_id: str):
        """Notify parents that child started conversation"""
        message = {
            "type": "conversation_started",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "status": "Child started talking to heyBuddy",
                "user_id": user_id
            }
        }
        await self.connection_manager.send_to_family(message, family_id)
    
    async def notify_conversation_ended(self, user_id: str, family_id: str, summary: Dict[str, Any]):
        """Notify parents when conversation ends with summary"""
        message = {
            "type": "conversation_ended", 
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "summary": summary,
                "duration_minutes": summary.get("duration_minutes", 0),
                "message_count": summary.get("message_count", 0),
                "topics": summary.get("topics", []),
                "emotional_support": summary.get("emotional_support_triggered", False)
            }
        }
        await self.connection_manager.send_to_family(message, family_id)
    
    async def notify_emotional_support(self, user_id: str, family_id: str, details: Dict[str, Any]):
        """Notify parents when emotional support is provided"""
        message = {
            "type": "emotional_support",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "high",
            "data": {
                "message": "Child received emotional support",
                "emotional_keywords": details.get("emotional_keywords", []),
                "support_provided": True,
                "needs_attention": True
            }
        }
        await self.connection_manager.send_to_family(message, family_id)
    
    async def notify_safety_alert(self, user_id: str, family_id: str, alert: Dict[str, Any]):
        """Notify parents of safety concerns"""
        message = {
            "type": "safety_alert",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "critical" if alert.get("crisis") else "medium",
            "data": {
                "level": alert.get("level", "medium"),
                "message": alert.get("message", "Safety alert triggered"),
                "action_required": alert.get("action_required", False),
                "details": alert
            }
        }
        await self.connection_manager.send_to_family(message, family_id)
    
    async def notify_goal_progress(self, user_id: str, family_id: str, goal: Dict[str, Any]):
        """Notify parents of goal progress"""
        message = {
            "type": "goal_progress",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "goal_title": goal.get("title", "Unknown Goal"),
                "progress_percent": goal.get("progress_percent", 0),
                "status": goal.get("status", "active"),
                "completed": goal.get("status") == "completed"
            }
        }
        await self.connection_manager.send_to_family(message, family_id)
    
    async def notify_device_status(self, status: Dict[str, Any]):
        """Notify all parents of device status changes"""
        message = {
            "type": "device_status",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "status": status.get("status", "unknown"),
                "audio_device": status.get("audio_device", "unknown"),
                "ai_service": status.get("ai_service", "healthy"),
                "uptime": status.get("uptime_hours", 0)
            }
        }
        await self.connection_manager.broadcast_to_all(message)


def create_websocket_routes(connection_manager: ConnectionManager):
    """Create WebSocket routes for the FastAPI app"""
    
    async def websocket_endpoint(websocket: WebSocket, family_id: str = "default"):
        """Main WebSocket endpoint for parental dashboard"""
        connection_id = str(uuid.uuid4())
        
        try:
            await connection_manager.connect(websocket, connection_id, family_id)
            
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for messages from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle client requests
                    if message.get("type") == "ping":
                        await connection_manager.send_personal_message({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }, connection_id)
                    
                    elif message.get("type") == "request_update":
                        # Client requesting latest data
                        await connection_manager.send_personal_message({
                            "type": "data_refresh_requested",
                            "timestamp": datetime.utcnow().isoformat()
                        }, connection_id)
                    
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from {connection_id}")
                except Exception as e:
                    logger.error(f"Error handling message from {connection_id}: {e}")
                    break
                    
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}")
        finally:
            connection_manager.disconnect(connection_id)
    
    return websocket_endpoint


class WebSocketManager:
    """Main WebSocket manager for the application"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.notifier = RealtimeNotifier(self.connection_manager)
        self.websocket_endpoint = create_websocket_routes(self.connection_manager)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "active_connections": len(self.connection_manager.active_connections),
            "family_connections": len(self.connection_manager.parent_connections),
            "families": list(self.connection_manager.parent_connections.keys())
        }