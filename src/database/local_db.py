"""
Local SQLite database manager for heyBuddy
All sensitive data stays local on device
"""
import logging
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import json
import uuid
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import base64
import os

from database.models import Base, User, ConversationSession, Conversation, Goal, GoalProgress
from core.config import settings

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Handle encryption for sensitive data"""
    
    def __init__(self, key: Optional[str] = None):
        if key:
            self.key = key.encode()
        else:
            # Generate or load encryption key
            self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Get existing encryption key or create new one"""
        key_file = "data/encryption.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Create new key
            os.makedirs("data", exist_ok=True)
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            logger.info("Generated new encryption key")
            return key
    
    def encrypt(self, text: str) -> str:
        """Encrypt text and return base64 encoded string"""
        if not text:
            return ""
        encrypted = self.cipher.encrypt(text.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt base64 encoded encrypted text"""
        if not encrypted_text:
            return ""
        try:
            encrypted = base64.b64decode(encrypted_text.encode())
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""


class LocalDatabase:
    """Local SQLite database manager"""
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or settings.database_url
        self.engine = None
        self.SessionLocal = None
        self.encryption = EncryptionManager()
        
    async def initialize(self) -> bool:
        """Initialize database connection and create tables"""
        try:
            # Create data directory if needed
            os.makedirs("data", exist_ok=True)
            
            # Create engine
            self.engine = create_engine(
                self.db_url,
                connect_args={"check_same_thread": False}  # For SQLite
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Test connection
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            
            logger.info("Local database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize local database: {e}")
            return False
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # User management
    def create_user(self, user_id: str, name: str, age: Optional[int] = None) -> User:
        """Create new user with encrypted data"""
        with self.get_session() as session:
            # Check if user exists
            existing = session.query(User).filter(User.id == user_id).first()
            if existing:
                return existing
            
            user = User(
                id=user_id,
                name_encrypted=self.encryption.encrypt(name),
                age=age,
                settings=json.dumps({
                    "persona": "friendly",
                    "safety_level": "standard",
                    "parent_notifications": True
                })
            )
            
            session.add(user)
            session.commit()
            logger.info(f"Created new user: {user_id}")
            return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        with self.get_session() as session:
            return session.query(User).filter(User.id == user_id).first()
    
    def get_user_name(self, user_id: str) -> Optional[str]:
        """Get decrypted user name"""
        user = self.get_user(user_id)
        if user and user.name_encrypted:
            return self.encryption.decrypt(user.name_encrypted)
        return None
    
    # Session management
    def start_conversation_session(self, user_id: str) -> ConversationSession:
        """Start new conversation session"""
        with self.get_session() as session:
            # End any existing active sessions
            active_sessions = session.query(ConversationSession).filter(
                ConversationSession.user_id == user_id,
                ConversationSession.end_time.is_(None)
            ).all()
            
            for active in active_sessions:
                active.end_time = datetime.utcnow()
                duration = (active.end_time - active.start_time).total_seconds() / 60
                active.duration_minutes = int(duration)
            
            # Create new session
            new_session = ConversationSession(
                id=str(uuid.uuid4()),
                user_id=user_id
            )
            
            session.add(new_session)
            session.commit()
            logger.info(f"Started conversation session for user {user_id}")
            return new_session
    
    def get_active_session(self, user_id: str) -> Optional[ConversationSession]:
        """Get active conversation session"""
        with self.get_session() as session:
            return session.query(ConversationSession).filter(
                ConversationSession.user_id == user_id,
                ConversationSession.end_time.is_(None)
            ).first()
    
    def end_conversation_session(self, session_id: str) -> Optional[ConversationSession]:
        """End conversation session"""
        with self.get_session() as session:
            conv_session = session.query(ConversationSession).filter(
                ConversationSession.id == session_id
            ).first()
            
            if conv_session:
                conv_session.end_time = datetime.utcnow()
                duration = (conv_session.end_time - conv_session.start_time).total_seconds() / 60
                conv_session.duration_minutes = int(duration)
                session.commit()
                logger.info(f"Ended conversation session {session_id}")
                return conv_session
            return None
    
    # Conversation storage
    def store_conversation(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Store conversation with encryption"""
        
        # Get or create session
        if not session_id:
            active_session = self.get_active_session(user_id)
            if not active_session:
                active_session = self.start_conversation_session(user_id)
            session_id = active_session.id
        
        with self.get_session() as session:
            # Update session metrics
            conv_session = session.query(ConversationSession).filter(
                ConversationSession.id == session_id
            ).first()
            
            if conv_session:
                conv_session.message_count += 1
                conv_session.last_activity = datetime.utcnow()
                
                # Add topic if provided in metadata
                if metadata and metadata.get("topic"):
                    conv_session.add_topic(metadata["topic"])
                
                # Track emotional support
                if metadata and metadata.get("emotional_support"):
                    conv_session.emotional_support_triggered = True
            
            # Create conversation record
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                session_id=session_id,
                user_message_encrypted=self.encryption.encrypt(user_message),
                ai_response_encrypted=self.encryption.encrypt(ai_response),
                message_type=metadata.get("type", "text") if metadata else "text",
                persona_used=metadata.get("persona", "friendly") if metadata else "friendly",
                emotional_support=metadata.get("emotional_support", False) if metadata else False,
                content_category=metadata.get("category") if metadata else None
            )
            
            session.add(conversation)
            session.commit()
            return conversation
    
    def get_conversation_history(
        self,
        user_id: str,
        limit: int = 10,
        decrypt: bool = False
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        with self.get_session() as session:
            conversations = session.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.timestamp.desc()).limit(limit).all()
            
            history = []
            for conv in conversations:
                conv_dict = {
                    "id": conv.id,
                    "timestamp": conv.timestamp.isoformat(),
                    "message_type": conv.message_type,
                    "persona_used": conv.persona_used,
                    "emotional_support": conv.emotional_support,
                    "content_category": conv.content_category
                }
                
                if decrypt:
                    conv_dict.update({
                        "user_message": self.encryption.decrypt(conv.user_message_encrypted),
                        "ai_response": self.encryption.decrypt(conv.ai_response_encrypted)
                    })
                
                history.append(conv_dict)
            
            return history
    
    # Goal management
    def create_goal(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        target_date: Optional[datetime] = None
    ) -> Goal:
        """Create new goal"""
        with self.get_session() as session:
            goal = Goal(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                description=description,
                category=category,
                target_date=target_date
            )
            
            session.add(goal)
            session.commit()
            logger.info(f"Created goal '{title}' for user {user_id}")
            return goal
    
    def update_goal_progress(
        self,
        goal_id: str,
        progress_percent: int,
        note: Optional[str] = None
    ) -> Optional[Goal]:
        """Update goal progress"""
        with self.get_session() as session:
            goal = session.query(Goal).filter(Goal.id == goal_id).first()
            if goal:
                goal.progress_percent = progress_percent
                if progress_percent >= 100:
                    goal.status = "completed"
                    goal.completed_at = datetime.utcnow()
                
                # Add progress entry
                progress_entry = GoalProgress(
                    id=str(uuid.uuid4()),
                    goal_id=goal_id,
                    progress_note=note,
                    progress_value=progress_percent
                )
                session.add(progress_entry)
                session.commit()
                return goal
            return None
    
    def get_user_goals(self, user_id: str, active_only: bool = True) -> List[Goal]:
        """Get user goals"""
        with self.get_session() as session:
            query = session.query(Goal).filter(Goal.user_id == user_id)
            if active_only:
                query = query.filter(Goal.status == "active")
            return query.order_by(Goal.created_at.desc()).all()
    
    # Analytics and summaries
    def get_session_summary(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get session summary for parental oversight"""
        with self.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            sessions = session.query(ConversationSession).filter(
                ConversationSession.user_id == user_id,
                ConversationSession.start_time >= cutoff_date
            ).all()
            
            total_sessions = len(sessions)
            total_messages = sum(s.message_count for s in sessions)
            total_duration = sum(s.duration_minutes for s in sessions)
            emotional_support_sessions = len([s for s in sessions if s.emotional_support_triggered])
            
            # Collect all topics
            all_topics = []
            for s in sessions:
                all_topics.extend(s.get_topics())
            
            unique_topics = list(set(all_topics))
            
            return {
                "period_days": days,
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "total_duration_minutes": total_duration,
                "emotional_support_sessions": emotional_support_sessions,
                "topics_discussed": unique_topics,
                "average_session_duration": total_duration / total_sessions if total_sessions > 0 else 0,
                "healthy_sessions": len([s for s in sessions if s.session_healthy])
            }
    
    async def cleanup(self):
        """Cleanup database resources"""
        if self.engine:
            self.engine.dispose()
            logger.info("Local database cleaned up")