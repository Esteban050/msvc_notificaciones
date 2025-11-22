"""
Unit tests for notification_service.py
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.notification_service import notification_service
from app.models.notification import (
    Notification,
    NotificationTemplate,
    UserNotificationPreference,
    NotificationType,
    NotificationStatus,
    NotificationPriority
)
from app.schemas.notification import NotificationEvent


@pytest.mark.unit
class TestNotificationService:
    """Test suite for NotificationService"""

    def test_get_user_preferences(self, db_session, sample_user_preference):
        """Test retrieving user preferences"""
        preferences = notification_service._get_user_preferences(
            db_session,
            str(sample_user_preference.user_id)
        )

        assert preferences is not None
        assert preferences.email_enabled == 1
        assert preferences.push_enabled == 1
        assert preferences.fcm_token == "sample-fcm-token-123"

    def test_get_user_preferences_not_found(self, db_session):
        """Test retrieving preferences for non-existent user"""
        preferences = notification_service._get_user_preferences(
            db_session,
            str(uuid4())
        )

        assert preferences is None

    def test_get_templates(self, db_session, sample_notification_template):
        """Test retrieving active templates for event type"""
        templates = notification_service._get_templates(
            db_session,
            "RESERVATION_CONFIRMED"
        )

        assert len(templates) >= 1
        assert templates[0].event_type == "RESERVATION_CONFIRMED"
        assert templates[0].is_active == 1

    def test_get_templates_no_results(self, db_session):
        """Test retrieving templates for non-existent event type"""
        templates = notification_service._get_templates(
            db_session,
            "NON_EXISTENT_EVENT"
        )

        assert len(templates) == 0

    def test_should_send_notification_no_preferences(self, sample_notification_template):
        """Test that notification is sent when no preferences exist"""
        result = notification_service._should_send_notification(
            preferences=None,
            template=sample_notification_template,
            event_type="RESERVATION_CONFIRMED"
        )

        assert result is True

    def test_should_send_notification_email_disabled(self, sample_user_preference, sample_notification_template):
        """Test that email notification is blocked when email disabled"""
        sample_user_preference.email_enabled = 0

        result = notification_service._should_send_notification(
            preferences=sample_user_preference,
            template=sample_notification_template,
            event_type="RESERVATION_CONFIRMED"
        )

        assert result is False

    def test_should_send_notification_push_disabled(self, sample_user_preference, db_session):
        """Test that push notification is blocked when push disabled"""
        sample_user_preference.push_enabled = 0

        push_template = NotificationTemplate(
            id=uuid4(),
            event_type="RESERVATION_CONFIRMED",
            notification_type=NotificationType.PUSH.value,
            subject="Test",
            body="Test body",
            is_active=1
        )

        result = notification_service._should_send_notification(
            preferences=sample_user_preference,
            template=push_template,
            event_type="RESERVATION_CONFIRMED"
        )

        assert result is False

    def test_should_send_notification_with_preferences_enabled(self, sample_user_preference, sample_notification_template):
        """Test that notification is sent when preferences are enabled"""
        result = notification_service._should_send_notification(
            preferences=sample_user_preference,
            template=sample_notification_template,
            event_type="RESERVATION_CONFIRMED"
        )

        assert result is True

    def test_render_template_with_placeholders(self):
        """Test template rendering with placeholder replacement"""
        template = NotificationTemplate(
            id=uuid4(),
            event_type="RESERVATION_CONFIRMED",
            notification_type=NotificationType.EMAIL.value,
            subject_template="Reservation at {parking_name}",
            body_template="Your reservation for {start_time} costs ${price}",
            is_active=1
        )

        data = {
            "parking_name": "Downtown Parking",
            "start_time": "2025-11-25T10:00:00Z",
            "price": 15.00
        }

        rendered = notification_service._render_template(template, data)

        assert rendered['subject'] == "Reservation at Downtown Parking"
        assert rendered['body'] == "Your reservation for 2025-11-25T10:00:00Z costs $15.0"

    def test_render_template_with_title(self):
        """Test template rendering with title for push notifications"""
        template = NotificationTemplate(
            id=uuid4(),
            event_type="PAYMENT_SUCCESS",
            notification_type=NotificationType.PUSH.value,
            title_template="Payment of ${amount} received",
            body_template="Thank you for your payment!",
            is_active=1
        )

        data = {"amount": 25.50}

        rendered = notification_service._render_template(template, data)

        assert rendered['title'] == "Payment of $25.5 received"
        assert rendered['body'] == "Thank you for your payment!"

    def test_replace_placeholders(self):
        """Test placeholder replacement logic"""
        template_str = "Hello {name}, your order {order_id} is ready"
        data = {"name": "John", "order_id": "12345"}

        result = notification_service._replace_placeholders(template_str, data)

        assert result == "Hello John, your order 12345 is ready"

    def test_replace_placeholders_missing_data(self):
        """Test placeholder replacement with missing data"""
        template_str = "Hello {name}, your order {order_id} is ready"
        data = {"name": "John"}

        result = notification_service._replace_placeholders(template_str, data)

        # Missing placeholders remain unchanged
        assert result == "Hello John, your order {order_id} is ready"

    def test_create_notification_email(self, db_session, sample_user_id):
        """Test creating an email notification record"""
        notification = notification_service._create_notification(
            db=db_session,
            user_id=sample_user_id,
            notification_type=NotificationType.EMAIL,
            event_type="RESERVATION_CONFIRMED",
            recipient_email="test@example.com",
            subject="Test Subject",
            body="Test body content",
            data={"key": "value"},
            priority=NotificationPriority.NORMAL
        )

        assert notification.id is not None
        assert str(notification.user_id) == sample_user_id
        assert notification.notification_type == NotificationType.EMAIL
        assert notification.event_type == "RESERVATION_CONFIRMED"
        assert notification.recipient_email == "test@example.com"
        assert notification.subject == "Test Subject"
        assert notification.body == "Test body content"
        assert notification.status == NotificationStatus.PENDING
        assert notification.priority == NotificationPriority.NORMAL

    def test_create_notification_push(self, db_session, sample_user_id):
        """Test creating a push notification record"""
        notification = notification_service._create_notification(
            db=db_session,
            user_id=sample_user_id,
            notification_type=NotificationType.PUSH,
            event_type="PAYMENT_SUCCESS",
            recipient_fcm_token="fcm-token-123",
            title="Payment Received",
            body="Your payment was successful",
            data={"amount": 50.0},
            priority=NotificationPriority.HIGH
        )

        assert notification.id is not None
        assert notification.notification_type == NotificationType.PUSH
        assert notification.recipient_fcm_token == "fcm-token-123"
        assert notification.title == "Payment Received"
        assert notification.priority == NotificationPriority.HIGH

    @pytest.mark.asyncio
    async def test_send_email_notification_success(self, db_session, sample_user_id):
        """Test successful email notification sending"""
        notification = notification_service._create_notification(
            db=db_session,
            user_id=sample_user_id,
            notification_type=NotificationType.EMAIL,
            event_type="TEST_EVENT",
            recipient_email="test@example.com",
            subject="Test",
            body="Test body",
            data={},
            priority=NotificationPriority.NORMAL
        )

        with patch('app.services.notification_service.email_service') as mock_email:
            mock_email.send_email = AsyncMock(return_value=True)
            mock_email.generate_html_template = MagicMock(return_value="<html>Test</html>")

            await notification_service._send_notification(db_session, notification)

            # Verify email service was called
            mock_email.send_email.assert_called_once()
            assert notification.status == NotificationStatus.SENT
            assert notification.sent_at is not None

    @pytest.mark.asyncio
    async def test_send_push_notification_success(self, db_session, sample_user_id):
        """Test successful push notification sending (no WebSocket connection)"""
        notification = notification_service._create_notification(
            db=db_session,
            user_id=sample_user_id,
            notification_type=NotificationType.PUSH,
            event_type="TEST_EVENT",
            recipient_fcm_token="fcm-token-123",
            title="Test",
            body="Test body",
            data={},
            priority=NotificationPriority.NORMAL
        )

        with patch('app.services.notification_service.push_service') as mock_push, \
             patch('app.websockets.connection_manager.manager') as mock_manager:

            mock_push.send_push_notification = AsyncMock(return_value=True)
            mock_manager.is_user_connected = MagicMock(return_value=False)

            await notification_service._send_notification(db_session, notification)

            # Verify push service was called
            mock_push.send_push_notification.assert_called_once_with(
                fcm_token="fcm-token-123",
                title="Test",
                body="Test body",
                data={}
            )
            assert notification.status == NotificationStatus.SENT

    @pytest.mark.asyncio
    async def test_send_push_notification_via_websocket(self, db_session, sample_user_id):
        """Test push notification sent via WebSocket when user is connected"""
        notification = notification_service._create_notification(
            db=db_session,
            user_id=sample_user_id,
            notification_type=NotificationType.PUSH,
            event_type="TEST_EVENT",
            recipient_fcm_token="fcm-token-123",
            title="Test",
            body="Test body",
            data={},
            priority=NotificationPriority.NORMAL
        )

        with patch('app.services.notification_service.push_service') as mock_push, \
             patch('app.websockets.connection_manager.manager') as mock_manager:

            mock_manager.is_user_connected = MagicMock(return_value=True)
            mock_manager.send_notification = AsyncMock(return_value=True)
            mock_push.send_push_notification = AsyncMock()

            await notification_service._send_notification(db_session, notification)

            # Verify WebSocket was used, NOT FCM
            mock_manager.send_notification.assert_called_once()
            mock_push.send_push_notification.assert_not_called()
            assert notification.status == NotificationStatus.SENT
            assert notification.data.get('sent_via') == 'websocket'

    @pytest.mark.asyncio
    async def test_handle_failed_notification_with_retries(self, db_session, sample_notification):
        """Test failed notification retry logic"""
        sample_notification.retry_count = 0
        sample_notification.max_retries = 3

        await notification_service._handle_failed_notification(
            db_session,
            sample_notification,
            "Connection timeout"
        )

        assert sample_notification.retry_count == 1
        assert sample_notification.status == NotificationStatus.RETRYING
        assert sample_notification.next_retry_at is not None
        assert sample_notification.error_message == "Connection timeout"

    @pytest.mark.asyncio
    async def test_handle_failed_notification_max_retries_reached(self, db_session, sample_notification):
        """Test notification marked as failed after max retries"""
        sample_notification.retry_count = 2
        sample_notification.max_retries = 3

        await notification_service._handle_failed_notification(
            db_session,
            sample_notification,
            "Final error"
        )

        assert sample_notification.retry_count == 3
        assert sample_notification.status == NotificationStatus.FAILED
        assert sample_notification.error_message == "Final error"

    @pytest.mark.asyncio
    async def test_send_notification_failure_triggers_retry(self, db_session, sample_user_id):
        """Test that failed notification triggers retry logic"""
        notification = notification_service._create_notification(
            db=db_session,
            user_id=sample_user_id,
            notification_type=NotificationType.EMAIL,
            event_type="TEST_EVENT",
            recipient_email="test@example.com",
            subject="Test",
            body="Test body",
            data={},
            priority=NotificationPriority.NORMAL
        )
        notification.max_retries = 3

        with patch('app.services.notification_service.email_service') as mock_email:
            mock_email.send_email = AsyncMock(return_value=False)
            mock_email.generate_html_template = MagicMock(return_value="<html>Test</html>")

            await notification_service._send_notification(db_session, notification)

            assert notification.status == NotificationStatus.RETRYING
            assert notification.retry_count == 1

    def test_process_event_integration(self, db_session, sample_notification_template,
                                       sample_user_preference, sample_notification_event):
        """Test end-to-end event processing (mocked sending)"""
        from app.schemas.notification import NotificationEvent

        event = NotificationEvent(**sample_notification_event)

        with patch('app.services.notification_service.SessionLocal', return_value=db_session), \
             patch('app.services.notification_service.email_service') as mock_email, \
             patch('app.services.notification_service.push_service') as mock_push:

            mock_email.send_email = AsyncMock(return_value=True)
            mock_email.generate_html_template = MagicMock(return_value="<html>Test</html>")
            mock_push.send_push_notification = AsyncMock(return_value=True)

            notification_service.process_event(event)

            # Verify notification was created in database
            notifications = db_session.query(Notification).all()
            assert len(notifications) > 0
