"""
Database models for AI Podcast Monitor.

Why these models?
- users: Single user for MVP, designed for multi-user scaling
- generation_contexts: Stores user's questionnaire answers per generation
- episodes: No channel FK (on-demand, not monitoring)
- summaries: Multiple summaries per episode (different users/contexts)
- user_interactions: Track behavior for future ML features
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """
    User accounts.

    MVP: Single user (id=1)
    Future: Multi-user with authentication
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    summaries = relationship("Summary", back_populates="user")
    interactions = relationship("UserInteraction", back_populates="user")
    generation_contexts = relationship("GenerationContext", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class GenerationContext(Base):
    """
    Stores user's questionnaire answers for each briefing generation.

    Why separate table from user preferences?
    - Users can experiment with different contexts for same episode
    - Enables A/B testing (which contexts produce better engagement)
    - Tracks evolution of user needs over time
    - Foundation for ML: predict best context based on episode content
    """
    __tablename__ = "generation_contexts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), index=True)
    summary_id = Column(Integer, ForeignKey("summaries.id"), nullable=True)

    # Question 1: What draws you to this episode?
    motivation = Column(String(50))  # "topic_interesting", "speaker_perspective", "personal_connection", "cultural_relevance"

    # Question 2: How deep should we go?
    depth_level = Column(String(50))  # "essence", "balanced", "deep"

    # Question 3: What kind of lens?
    reasoning_mode = Column(String(50))  # "connect", "challenge", "apply", "reflect"

    # Question 4: Which voice feels right?
    narrative_tone = Column(String(50))  # "analytical", "conversational", "thoughtful", "provocative"

    # Question 5: Anything you're curious about? (optional)
    curiosity_focus = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="generation_contexts")
    episode = relationship("Episode", back_populates="generation_contexts")
    summary = relationship("Summary", back_populates="generation_context", uselist=False)

    def __repr__(self):
        return f"<GenerationContext(id={self.id}, motivation={self.motivation}, depth={self.depth_level})>"


class Episode(Base):
    """
    Podcast episodes from YouTube.

    Note: No channel_id FK because we don't track channels in on-demand MVP.
    channel_name extracted from YouTube metadata instead.
    """
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(255), unique=True, index=True)  # YouTube video ID
    channel_name = Column(String(255), index=True)  # For grouping/filtering
    title = Column(String(500))
    description = Column(Text, nullable=True)
    published_at = Column(DateTime)
    duration = Column(Integer)  # seconds
    thumbnail_url = Column(String(500))
    video_url = Column(String(500))
    transcript = Column(Text, nullable=True)  # Cached caption text
    created_at = Column(DateTime, default=datetime.utcnow)  # When first requested

    # Relationships
    summaries = relationship("Summary", back_populates="episode")
    interactions = relationship("UserInteraction", back_populates="episode")
    generation_contexts = relationship("GenerationContext", back_populates="episode")

    def __repr__(self):
        return f"<Episode(id={self.id}, title={self.title[:50]})>"


class Summary(Base):
    """
    Personalized summaries for episodes.

    Why multiple summaries per episode?
    - Different users (multi-user)
    - Same user, different preferences (experimentation)
    - A/B testing (which prompt works better)
    """
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    summary_text = Column(Text)  # Markdown format
    key_topics = Column(JSON, default=list)  # ["AI", "regulation", "ethics"]
    preferences_used = Column(JSON, default=dict)  # Snapshot: {"interests": ["tech"]}
    token_count = Column(Integer, default=0)  # Cost tracking
    generation_time = Column(Float, default=0.0)  # Latency tracking (seconds)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    episode = relationship("Episode", back_populates="summaries")
    user = relationship("User", back_populates="summaries")
    generation_context = relationship("GenerationContext", back_populates="summary", uselist=False)

    def __repr__(self):
        return f"<Summary(id={self.id}, episode_id={self.episode_id})>"


class UserInteraction(Base):
    """
    Track user behavior for analytics and future ML features.

    Why track from day 1?
    - ML models need 6+ months of data
    - Build training dataset NOW for models LATER
    - Identify popular podcasts for pre-caching
    """
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=True, index=True)
    action_type = Column(String(50), index=True)  # "search", "view", "read", "summarize"
    interaction_metadata = Column(JSON, default=dict)  # {"search_query": "joe rogan", "time_spent": 120}
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="interactions")
    episode = relationship("Episode", back_populates="interactions")

    def __repr__(self):
        return f"<UserInteraction(id={self.id}, action={self.action_type})>"
