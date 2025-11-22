from sqlalchemy import Column, String, DateTime, Enum, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from app.database.connection import Base


class NotificationType(str, enum.Enum):
    EMAIL = "email"
    PUSH = "push"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    notification_type = Column(Enum(NotificationType), nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False)

    # Recipient information
    recipient_email = Column(String(255))
    recipient_fcm_token = Column(String(500))

    # Content
    subject = Column(String(255))
    title = Column(String(255))
    body = Column(Text, nullable=False)
    data = Column(JSON)  # Additional metadata

    # Event information
    event_type = Column(String(100), nullable=False, index=True)

    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Error tracking
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.id} - {self.notification_type} - {self.status}>"


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), unique=True, nullable=False, index=True)
    notification_type = Column(Enum(NotificationType), nullable=False)

    # Template content
    subject_template = Column(String(255))  # For email
    title_template = Column(String(255))    # For push
    body_template = Column(Text, nullable=False)

    # Configuration
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)
    is_active = Column(Integer, default=1)  # Using Integer for boolean (0 or 1)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<NotificationTemplate {self.event_type} - {self.notification_type}>"


class UserNotificationPreference(Base):
    __tablename__ = "user_notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)

    # FCM Token for push notifications
    fcm_token = Column(String(500))

    # Preferences by event type
    email_enabled = Column(Integer, default=1)  # 0 = disabled, 1 = enabled
    push_enabled = Column(Integer, default=1)

    # Specific event preferences (JSON structure)
    # Example: {"RESERVATION_CONFIRMED": {"email": true, "push": true}}
    event_preferences = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserNotificationPreference {self.user_id}>"
