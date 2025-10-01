"""
Database models for YouTube Channel Subscription and Video Management System.

This module defines SQLAlchemy models for storing channels, videos, captions, and summaries.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class ProcessingStatus(enum.Enum):
    """Processing status for videos."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Channel(Base):
    """
    YouTube channel model.

    Stores information about subscribed YouTube channels.
    """
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(255), unique=True, nullable=False, index=True)
    channel_name = Column(String(255), nullable=False)
    channel_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to videos
    videos = relationship("Video", back_populates="channel", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Channel(id={self.id}, channel_name='{self.channel_name}', channel_id='{self.channel_id}')>"

    def to_dict(self):
        """Convert channel to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'channel_id': self.channel_id,
            'channel_name': self.channel_name,
            'channel_url': self.channel_url,
            'thumbnail_url': self.thumbnail_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'video_count': len(self.videos) if self.videos else 0
        }


class Video(Base):
    """
    YouTube video model.

    Stores video metadata, captions, and AI-generated summaries.
    """
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey('channels.id', ondelete='CASCADE'), nullable=False, index=True)
    video_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True, index=True)
    caption_text = Column(Text, nullable=True)
    short_summary = Column(Text, nullable=True)
    detailed_summary = Column(Text, nullable=True)
    processing_status = Column(
        Enum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False,
        index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to channel
    channel = relationship("Channel", back_populates="videos")

    # Indexes for common queries
    __table_args__ = (
        Index('ix_videos_channel_published', 'channel_id', 'published_at'),
        Index('ix_videos_status_created', 'processing_status', 'created_at'),
    )

    def __repr__(self):
        return f"<Video(id={self.id}, video_id='{self.video_id}', title='{self.title[:50]}...', status='{self.processing_status}')>"

    def to_dict(self, include_detailed=False):
        """
        Convert video to dictionary for JSON serialization.

        Args:
            include_detailed: If True, includes caption_text and detailed_summary.
                             If False, only includes basic info and short_summary (for list views).
        """
        base_dict = {
            'id': self.id,
            'channel_id': self.channel_id,
            'video_id': self.video_id,
            'title': self.title,
            'thumbnail_url': self.thumbnail_url,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'short_summary': self.short_summary,
            'processing_status': self.processing_status.value if self.processing_status else 'pending',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        # Include channel name if available
        if self.channel:
            base_dict['channel_name'] = self.channel.channel_name

        # Include detailed information if requested (for detail view)
        if include_detailed:
            base_dict.update({
                'caption_text': self.caption_text,
                'detailed_summary': self.detailed_summary,
            })

        return base_dict