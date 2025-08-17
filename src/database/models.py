"""
Database models for heyBuddy
Supports both SQLite (local) and Supabase (optional sync)
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
import json

Base = declarative_base()


class User(Base):
    """User profile - stored locally only for privacy"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Locally generated UUID
    name_encrypted = Column(String, nullable=False)  # Encrypted name
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Settings stored as JSON
    settings = Column(Text, default="{}")  # JSON string
    preferences = Column(Text, default="{}")  # JSON string
    
    # Privacy settings
    parental_sync_enabled = Column(Boolean, default=False)
    data_sharing_consent = Column(Boolean, default=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    sessions = relationship("ConversationSession", back_populates="user")
    
    def get_settings(self) -> dict:
        """Get user settings as dict"""
        return json.loads(self.settings) if self.settings else {}
    
    def set_settings(self, settings_dict: dict):
        """Set user settings from dict"""
        self.settings = json.dumps(settings_dict)


class ConversationSession(Base):
    """Conversation session tracking - local only"""
    __tablename__ = "conversation_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    # Session metrics
    message_count = Column(Integer, default=0)
    safety_warnings = Column(Integer, default=0)
    emotional_support_triggered = Column(Boolean, default=False)
    
    # Topics discussed (high-level only)
    topics = Column(Text, default="[]")  # JSON array
    emotional_keywords = Column(Text, default="[]")  # JSON array
    
    # Health indicators
    session_healthy = Column(Boolean, default=True)
    duration_minutes = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    conversations = relationship("Conversation", back_populates="session")
    
    def get_topics(self) -> list:
        return json.loads(self.topics) if self.topics else []
    
    def add_topic(self, topic: str):
        topics = self.get_topics()
        if topic not in topics:
            topics.append(topic)
        self.topics = json.dumps(topics)


class Conversation(Base):
    """Individual conversations - stored locally with privacy protection"""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, ForeignKey("conversation_sessions.id"), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Content (encrypted for privacy)
    user_message_encrypted = Column(Text, nullable=True)
    ai_response_encrypted = Column(Text, nullable=True)
    
    # Metadata (not encrypted - for analysis)
    message_type = Column(String, default="text")  # text, voice, story
    persona_used = Column(String, default="friendly")
    
    # Safety metadata
    input_flagged = Column(Boolean, default=False)
    output_flagged = Column(Boolean, default=False)
    emotional_support = Column(Boolean, default=False)
    
    # Content categories (safe to store)
    content_category = Column(String, nullable=True)  # education, emotional, play, etc.
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    session = relationship("ConversationSession", back_populates="conversations")


class Goal(Base):
    """User goals and achievements"""
    __tablename__ = "goals"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # routine, learning, emotional, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    target_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Progress tracking
    status = Column(String, default="active")  # active, completed, paused
    progress_percent = Column(Integer, default=0)
    
    # Sync status for parent dashboard
    sync_to_parent = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="goals")
    progress_entries = relationship("GoalProgress", back_populates="goal")


class GoalProgress(Base):
    """Goal progress tracking"""
    __tablename__ = "goal_progress"
    
    id = Column(String, primary_key=True)
    goal_id = Column(String, ForeignKey("goals.id"), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    progress_note = Column(Text, nullable=True)
    progress_value = Column(Float, nullable=True)  # Numeric progress if applicable
    
    # How progress was recorded
    recorded_by = Column(String, default="ai")  # ai, user, parent
    
    # Relationships
    goal = relationship("Goal", back_populates="progress_entries")


# Supabase sync models (metadata only, no personal data)
class SyncSessionSummary(Base):
    """Session summaries for parental dashboard - safe for cloud sync"""
    __tablename__ = "sync_session_summaries"
    
    id = Column(String, primary_key=True)
    device_id = Column(String, nullable=False)  # Pi device identifier
    user_hash = Column(String, nullable=False)  # Hashed user ID
    
    session_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    
    # Safe metadata only
    topics_count = Column(Integer, default=0)
    emotional_support = Column(Boolean, default=False)
    safety_warnings = Column(Integer, default=0)
    session_healthy = Column(Boolean, default=True)
    
    # General content categories (no specific content)
    content_categories = Column(Text, default="[]")  # JSON array
    
    sync_timestamp = Column(DateTime, default=datetime.utcnow)


class SyncGoalSummary(Base):
    """Goal summaries for parental dashboard"""
    __tablename__ = "sync_goal_summaries"
    
    id = Column(String, primary_key=True)
    device_id = Column(String, nullable=False)
    user_hash = Column(String, nullable=False)
    
    goal_title = Column(String, nullable=False)
    goal_category = Column(String, nullable=True)
    status = Column(String, nullable=False)
    progress_percent = Column(Integer, default=0)
    
    created_date = Column(DateTime, nullable=False)
    target_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    
    sync_timestamp = Column(DateTime, default=datetime.utcnow)


class DeviceStatus(Base):
    """Device status for parental monitoring"""
    __tablename__ = "device_status"
    
    device_id = Column(String, primary_key=True)
    device_name = Column(String, nullable=True)
    
    last_seen = Column(DateTime, default=datetime.utcnow)
    software_version = Column(String, nullable=True)
    
    # Health metrics
    uptime_hours = Column(Float, default=0)
    audio_device_status = Column(String, default="unknown")
    ai_service_status = Column(String, default="unknown")
    
    # Usage metrics (anonymized)
    daily_active_users = Column(Integer, default=0)
    total_conversations_today = Column(Integer, default=0)
    
    sync_timestamp = Column(DateTime, default=datetime.utcnow)