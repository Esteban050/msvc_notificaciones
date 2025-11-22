"""
Pytest configuration and global fixtures for ms-notifications tests
"""
import os
import pytest
from datetime import datetime
from uuid import uuid4
from typing import Generator
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database.connection import Base, get_db
from app.main import app
from app.models.notification import (
    Notification,
    NotificationTemplate,
    UserNotificationPreference,
    NotificationType,
    NotificationStatus,
    NotificationPriority
)

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    Uses SQLite in-memory database for speed.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with overridden database dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Mock fixtures for external services

@pytest.fixture
def mock_firebase():
    """Mock Firebase Admin SDK"""
    mock_firebase = MagicMock()
    mock_firebase.initialize_app = MagicMock()
    mock_firebase.messaging.send = MagicMock(return_value="message-id-123")
    mock_firebase.messaging.send_multicast = MagicMock(
        return_value=MagicMock(success_count=1, failure_count=0)
    )
    return mock_firebase


@pytest.fixture
def mock_smtp():
    """Mock aiosmtplib SMTP client"""
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.login = AsyncMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.quit = AsyncMock()
    return mock_smtp


@pytest.fixture
def mock_rabbitmq():
    """Mock pika RabbitMQ client"""
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_connection.channel.return_value = mock_channel

    mock_rabbitmq = MagicMock()
    mock_rabbitmq.BlockingConnection.return_value = mock_connection
    mock_rabbitmq.URLParameters.return_value = MagicMock()
    mock_rabbitmq.ConnectionParameters.return_value = MagicMock()

    return {
        'connection': mock_connection,
        'channel': mock_channel,
        'pika': mock_rabbitmq
    }


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket connection manager"""
    mock_manager = AsyncMock()
    mock_manager.is_user_connected = AsyncMock(return_value=False)
    mock_manager.send_personal_message = AsyncMock()
    return mock_manager


# Sample data fixtures

@pytest.fixture
def sample_user_id():
    """Generate a sample UUID for user"""
    return uuid4()


@pytest.fixture
def sample_user_email() -> str:
    """Sample user email"""
    return "test@example.com"


@pytest.fixture
def sample_notification_template(db_session: Session) -> NotificationTemplate:
    """Create a sample notification template"""
    template = NotificationTemplate(
        id=uuid4(),
        event_type="RESERVATION_CONFIRMED",
        notification_type=NotificationType.EMAIL.value,
        subject="Reservation Confirmed - {parking_name}",
        body="Your reservation at {parking_name} is confirmed for {start_time}. Total: ${price}",
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def sample_push_template(db_session: Session) -> NotificationTemplate:
    """Create a sample push notification template"""
    template = NotificationTemplate(
        id=uuid4(),
        event_type="RESERVATION_CONFIRMED",
        notification_type=NotificationType.PUSH.value,
        subject="Reservation Confirmed",
        body="Your reservation at {parking_name} is confirmed!",
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def sample_user_preference(db_session: Session, sample_user_id) -> UserNotificationPreference:
    """Create sample user notification preferences"""
    preference = UserNotificationPreference(
        id=uuid4(),
        user_id=sample_user_id,
        email_enabled=1,
        push_enabled=1,
        fcm_token="sample-fcm-token-123",
        reservation_notifications=1,
        payment_notifications=1,
        marketing_notifications=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(preference)
    db_session.commit()
    db_session.refresh(preference)
    return preference


@pytest.fixture
def sample_notification(db_session: Session, sample_user_id) -> Notification:
    """Create a sample notification record"""
    notification = Notification(
        id=uuid4(),
        user_id=sample_user_id,
        notification_type=NotificationType.EMAIL.value,
        event_type="RESERVATION_CONFIRMED",
        subject="Test Subject",
        body="Test body content",
        status=NotificationStatus.PENDING.value,
        priority=NotificationPriority.NORMAL.value,
        retry_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


@pytest.fixture
def sample_event_data() -> dict:
    """Sample event data for testing"""
    return {
        "parking_name": "Downtown Parking Lot",
        "start_time": "2025-11-25T10:00:00Z",
        "end_time": "2025-11-25T18:00:00Z",
        "price": 15.00,
        "spot_number": "A-123"
    }


@pytest.fixture
def sample_notification_event(sample_user_id, sample_user_email: str, sample_event_data: dict) -> dict:
    """Complete notification event payload"""
    return {
        "user_id": str(sample_user_id),
        "user_email": sample_user_email,
        "event_type": "RESERVATION_CONFIRMED",
        "data": sample_event_data
    }
