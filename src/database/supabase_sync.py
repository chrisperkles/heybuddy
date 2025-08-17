"""
Supabase sync manager for heyBuddy parental dashboard
Syncs only anonymized metadata, never personal conversations
"""
import logging
import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import httpx
from core.config import settings

logger = logging.getLogger(__name__)


class SupabaseSync:
    """Manages sync of anonymized data to Supabase for parental dashboard"""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        self.supabase_url = supabase_url or getattr(settings, 'supabase_url', None)
        self.supabase_key = supabase_key or getattr(settings, 'supabase_key', None)
        self.device_id = self._get_device_id()
        self.enabled = bool(self.supabase_url and self.supabase_key)
        
        if not self.enabled:
            logger.info("Supabase sync disabled - no credentials provided")
    
    def _get_device_id(self) -> str:
        """Get unique device identifier"""
        # In production, this could be MAC address hash or Pi serial number
        import platform
        import uuid
        node_id = str(uuid.getnode())
        hostname = platform.node()
        combined = f"{hostname}-{node_id}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _hash_user_id(self, user_id: str) -> str:
        """Create privacy-safe hash of user ID"""
        # Add device salt for extra privacy
        salted = f"{self.device_id}-{user_id}"
        return hashlib.sha256(salted.encode()).hexdigest()[:16]
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request to Supabase"""
        if not self.enabled:
            return None
        
        url = f"{self.supabase_url}/rest/v1/{endpoint}"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, headers=headers, json=data)
                elif method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None
                
                if response.status_code in [200, 201, 204]:
                    return response.json() if response.content else {}
                else:
                    logger.error(f"Supabase request failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Supabase request error: {e}")
            return None
    
    async def sync_session_summary(
        self,
        user_id: str,
        session_data: Dict[str, Any]
    ) -> bool:
        """Sync anonymized session summary"""
        if not self.enabled:
            return False
        
        # Create privacy-safe summary
        summary = {
            "device_id": self.device_id,
            "user_hash": self._hash_user_id(user_id),
            "session_date": session_data.get("start_time", datetime.utcnow()).isoformat(),
            "duration_minutes": session_data.get("duration_minutes", 0),
            "message_count": session_data.get("message_count", 0),
            "topics_count": len(session_data.get("topics", [])),
            "emotional_support": session_data.get("emotional_support_triggered", False),
            "safety_warnings": session_data.get("safety_warnings", 0),
            "session_healthy": session_data.get("session_healthy", True),
            "content_categories": json.dumps(session_data.get("content_categories", [])),
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self._make_request("POST", "sync_session_summaries", summary)
        success = result is not None
        
        if success:
            logger.info(f"Synced session summary for user hash {summary['user_hash']}")
        
        return success
    
    async def sync_goal_summary(
        self,
        user_id: str,
        goal_data: Dict[str, Any]
    ) -> bool:
        """Sync anonymized goal summary"""
        if not self.enabled:
            return False
        
        # Create privacy-safe goal summary
        goal_summary = {
            "device_id": self.device_id,
            "user_hash": self._hash_user_id(user_id),
            "goal_title": goal_data.get("title", "")[:50],  # Truncate for privacy
            "goal_category": goal_data.get("category"),
            "status": goal_data.get("status", "active"),
            "progress_percent": goal_data.get("progress_percent", 0),
            "created_date": goal_data.get("created_at", datetime.utcnow()).isoformat(),
            "target_date": goal_data.get("target_date").isoformat() if goal_data.get("target_date") else None,
            "completed_date": goal_data.get("completed_at").isoformat() if goal_data.get("completed_at") else None,
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self._make_request("POST", "sync_goal_summaries", goal_summary)
        success = result is not None
        
        if success:
            logger.info(f"Synced goal summary: {goal_summary['goal_title']}")
        
        return success
    
    async def sync_device_status(
        self,
        device_name: Optional[str] = None,
        software_version: Optional[str] = None,
        health_metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Sync device status for monitoring"""
        if not self.enabled:
            return False
        
        status = {
            "device_id": self.device_id,
            "device_name": device_name or f"heyBuddy-{self.device_id[:8]}",
            "last_seen": datetime.utcnow().isoformat(),
            "software_version": software_version or settings.version,
            "uptime_hours": health_metrics.get("uptime_hours", 0) if health_metrics else 0,
            "audio_device_status": health_metrics.get("audio_status", "unknown") if health_metrics else "unknown",
            "ai_service_status": health_metrics.get("ai_status", "unknown") if health_metrics else "unknown",
            "daily_active_users": health_metrics.get("daily_users", 0) if health_metrics else 0,
            "total_conversations_today": health_metrics.get("conversations_today", 0) if health_metrics else 0,
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
        # Use PATCH to update existing device or POST to create new
        result = await self._make_request("POST", "device_status", status)
        success = result is not None
        
        if success:
            logger.info(f"Synced device status for {status['device_name']}")
        
        return success
    
    async def get_family_dashboard_data(self, family_hash: str) -> Optional[Dict[str, Any]]:
        """Get dashboard data for family (parent web app)"""
        if not self.enabled:
            return None
        
        try:
            # Get recent session summaries
            sessions_response = await self._make_request(
                "GET",
                f"sync_session_summaries?device_id=eq.{self.device_id}&order=session_date.desc&limit=10"
            )
            
            # Get goal summaries
            goals_response = await self._make_request(
                "GET", 
                f"sync_goal_summaries?device_id=eq.{self.device_id}&order=created_date.desc&limit=20"
            )
            
            # Get device status
            device_response = await self._make_request(
                "GET",
                f"device_status?device_id=eq.{self.device_id}"
            )
            
            return {
                "device_id": self.device_id,
                "recent_sessions": sessions_response or [],
                "goals": goals_response or [],
                "device_status": device_response[0] if device_response else {},
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return None
    
    async def test_connection(self) -> bool:
        """Test Supabase connection"""
        if not self.enabled:
            logger.warning("Supabase not configured")
            return False
        
        try:
            result = await self._make_request("GET", "device_status?limit=1")
            success = result is not None
            
            if success:
                logger.info("Supabase connection test successful")
            else:
                logger.error("Supabase connection test failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Supabase connection test error: {e}")
            return False


class SyncManager:
    """Manages sync operations between local DB and Supabase"""
    
    def __init__(self, local_db, supabase_sync: SupabaseSync):
        self.local_db = local_db
        self.supabase = supabase_sync
        self.sync_enabled = supabase_sync.enabled
        self.last_sync = None
        
    async def sync_user_session(self, user_id: str, session_id: str) -> bool:
        """Sync completed session to cloud"""
        if not self.sync_enabled:
            return False
        
        try:
            # Get session from local DB
            with self.local_db.get_session() as session:
                conv_session = session.query(ConversationSession).filter(
                    ConversationSession.id == session_id
                ).first()
                
                if not conv_session:
                    return False
                
                # Check if user has sync enabled
                user = session.query(User).filter(User.id == user_id).first()
                if not user or not user.parental_sync_enabled:
                    logger.info(f"Sync disabled for user {user_id}")
                    return False
                
                # Prepare session data for sync
                session_data = {
                    "start_time": conv_session.start_time,
                    "duration_minutes": conv_session.duration_minutes,
                    "message_count": conv_session.message_count,
                    "topics": conv_session.get_topics(),
                    "emotional_support_triggered": conv_session.emotional_support_triggered,
                    "safety_warnings": conv_session.safety_warnings,
                    "session_healthy": conv_session.session_healthy,
                    "content_categories": self._extract_content_categories(conv_session)
                }
                
                # Sync to Supabase
                success = await self.supabase.sync_session_summary(user_id, session_data)
                return success
                
        except Exception as e:
            logger.error(f"Error syncing user session: {e}")
            return False
    
    async def sync_user_goal(self, user_id: str, goal_id: str) -> bool:
        """Sync goal to cloud"""
        if not self.sync_enabled:
            return False
        
        try:
            # Get goal from local DB
            with self.local_db.get_session() as session:
                goal = session.query(Goal).filter(Goal.id == goal_id).first()
                
                if not goal or not goal.sync_to_parent:
                    return False
                
                # Check if user has sync enabled
                user = session.query(User).filter(User.id == user_id).first()
                if not user or not user.parental_sync_enabled:
                    return False
                
                # Prepare goal data for sync
                goal_data = {
                    "title": goal.title,
                    "category": goal.category,
                    "status": goal.status,
                    "progress_percent": goal.progress_percent,
                    "created_at": goal.created_at,
                    "target_date": goal.target_date,
                    "completed_at": goal.completed_at
                }
                
                # Sync to Supabase
                success = await self.supabase.sync_goal_summary(user_id, goal_data)
                return success
                
        except Exception as e:
            logger.error(f"Error syncing goal: {e}")
            return False
    
    def _extract_content_categories(self, session) -> List[str]:
        """Extract general content categories from session"""
        # This would analyze conversation metadata to determine categories
        # without exposing actual content
        categories = []
        
        topics = session.get_topics()
        for topic in topics:
            if any(keyword in topic.lower() for keyword in ["story", "tale", "adventure"]):
                categories.append("storytelling")
            elif any(keyword in topic.lower() for keyword in ["scared", "afraid", "worry", "emotion"]):
                categories.append("emotional_support")
            elif any(keyword in topic.lower() for keyword in ["school", "homework", "learn"]):
                categories.append("education")
            elif any(keyword in topic.lower() for keyword in ["play", "game", "fun"]):
                categories.append("play")
            else:
                categories.append("general")
        
        return list(set(categories))
    
    async def periodic_sync(self):
        """Perform periodic sync of device status"""
        if not self.sync_enabled:
            return
        
        try:
            # Collect health metrics
            health_metrics = {
                "uptime_hours": self._get_uptime_hours(),
                "audio_status": "healthy",  # Would check actual audio status
                "ai_status": "healthy",     # Would check AI service status
                "daily_users": self._get_daily_user_count(),
                "conversations_today": self._get_daily_conversation_count()
            }
            
            await self.supabase.sync_device_status(
                health_metrics=health_metrics
            )
            
            self.last_sync = datetime.utcnow()
            logger.info("Periodic sync completed")
            
        except Exception as e:
            logger.error(f"Periodic sync error: {e}")
    
    def _get_uptime_hours(self) -> float:
        """Get system uptime in hours"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                return uptime_seconds / 3600
        except:
            return 0.0
    
    def _get_daily_user_count(self) -> int:
        """Get number of active users today"""
        try:
            today = datetime.utcnow().date()
            with self.local_db.get_session() as session:
                count = session.query(ConversationSession).filter(
                    ConversationSession.start_time >= today
                ).distinct(ConversationSession.user_id).count()
                return count
        except:
            return 0
    
    def _get_daily_conversation_count(self) -> int:
        """Get total conversations today"""
        try:
            today = datetime.utcnow().date()
            with self.local_db.get_session() as session:
                count = session.query(Conversation).filter(
                    Conversation.timestamp >= today
                ).count()
                return count
        except:
            return 0