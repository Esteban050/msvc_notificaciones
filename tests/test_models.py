"""
Unit tests for database models
"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.models.notification import (
    Notification,
    NotificationTemplate,
    UserNotificationPreference,
    NotificationType,
    NotificationStatus,
    NotificationPriority
)


@pytest.mark.unit
class TestNotificationModels:
    """Test suite for notification database models"""

    def test_create_notification_email(self, db_session, sample_user_id):
        """Test creating an email notification record"""
        notification = Notification(
            user_id=sample_user_id,
            notification_type=NotificationType.EMAIL.value,
            event_type="RESERVATION_CONFIRMED",
            recipient_email="test@example.com",
            subject="Test Subject",
            body="Test body content",
            status=NotificationStatus.PENDING.value,
            priority=NotificationPriority.NORMAL.value,
            data={"key": "value"}
        )

        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        assert notification.id is not None
        assert notification.user_id == sample_user_id
        assert notification.notification_type == NotificationType.EMAIL.value
        assert notification.event_type == "RESERVATION_CONFIRMED"
        assert notification.recipient_email == "test@example.com"
        assert notification.subject == "Test Subject"
        assert notification.body == "Test body content"
        assert notification.status == NotificationStatus.PENDING.value
        assert notification.priority == NotificationPriority.NORMAL.value
        assert notification.retry_count == 0
        assert notification.created_at is not None
        assert notification.updated_at is not None

    def test_create_notification_push(self, db_session, sample_user_id):
        """Test creating a push notification record"""
        notification = Notification(
            user_id=sample_user_id,
            notification_type=NotificationType.PUSH.value,
            event_type="PAYMENT_SUCCESS",
            recipient_fcm_token="fcm-token-123",
            title="Payment Received",
            body="Your payment was successful",
            status=NotificationStatus.SENT.value,
            priority=NotificationPriority.HIGH.value,
            data={"amount": 50.0}
        )

        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        assert notification.notification_type == NotificationType.PUSH.value
        assert notification.recipient_fcm_token == "fcm-token-123"
        assert notification.title == "Payment Received"
        assert notification.priority == NotificationPriority.HIGH.value

    def test_notification_status_enum(self, db_session, sample_user_id):
        """Test notification status transitions"""
        notification = Notification(
            user_id=sample_user_id,
            notification_type=NotificationType.EMAIL.value,
            event_type="TEST_EVENT",
            recipient_email="test@example.com",
            subject="Test",
            body="Body",
            status=NotificationStatus.PENDING.value,
            priority=NotificationPriority.NORMAL.value
        )

        db_session.add(notification)
        db_session.commit()

        # Change status to SENT
        notification.status = NotificationStatus.SENT.value
        notification.sent_at = datetime.utcnow()
        db_session.commit()

        assert notification.status == NotificationStatus.SENT.value
        assert notification.sent_at is not None

        # Query and verify
        retrieved = db_session.query(Notification).filter_by(id=notification.id).first()
        assert retrieved.status == NotificationStatus.SENT.value

    def test_notification_retry_logic(self, db_session, sample_user_id):
        """Test notification retry count and error tracking"""
        notification = Notification(
            user_id=sample_user_id,
            notification_type=NotificationType.EMAIL.value,
            event_type="TEST_EVENT",
            recipient_email="test@example.com",
            subject="Test",
            body="Body",
            status=NotificationStatus.RETRYING.value,
            priority=NotificationPriority.NORMAL.value,
            retry_count=2,
            max_retries=3,
            error_message="Connection timeout"
        )

        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        assert notification.retry_count == 2
        assert notification.max_retries == 3
        assert notification.error_message == "Connection timeout"
        assert notification.status == NotificationStatus.RETRYING.value

    def test_notification_priority_enum(self, db_session, sample_user_id):
        """Test different notification priorities"""
        priorities = [
            NotificationPriority.LOW,
            NotificationPriority.NORMAL,
            NotificationPriority.HIGH,
            NotificationPriority.URGENT
        ]

        for priority in priorities:
            notification = Notification(
                user_id=sample_user_id,
                notification_type=NotificationType.EMAIL.value,
                event_type="TEST_EVENT",
                recipient_email="test@example.com",
                subject="Test",
                body="Body",
                status=NotificationStatus.PENDING.value,
                priority=priority.value
            )

            db_session.add(notification)
            db_session.commit()
            db_session.refresh(notification)

            assert notification.priority == priority.value

        # Verify all were created
        all_notifications = db_session.query(Notification).all()
        assert len(all_notifications) >= 4

    def test_create_notification_template(self, db_session):
        """Test creating a notification template"""
        template = NotificationTemplate(
            event_type="RESERVATION_CONFIRMED",
            notification_type=NotificationType.EMAIL.value,
            subject_template="Reservation at {parking_name}",
            body_template="Your reservation is confirmed for {start_time}",
            is_active=1,
            priority=NotificationPriority.NORMAL.value
        )

        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        assert template.id is not None
        assert template.event_type == "RESERVATION_CONFIRMED"
        assert template.notification_type == NotificationType.EMAIL.value
        assert "{parking_name}" in template.subject_template
        assert "{start_time}" in template.body_template
        assert template.is_active == 1
        assert template.created_at is not None

    def test_notification_template_push(self, db_session):
        """Test creating a push notification template"""
        template = NotificationTemplate(
            event_type="PAYMENT_SUCCESS",
            notification_type=NotificationType.PUSH.value,
            title_template="Payment of ${amount} received",
            body_template="Thank you for your payment!",
            is_active=1,
            priority=NotificationPriority.HIGH.value
        )

        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        assert template.notification_type == NotificationType.PUSH.value
        assert template.title_template == "Payment of ${amount} received"
        assert template.priority == NotificationPriority.HIGH.value

    def test_notification_template_inactive(self, db_session):
        """Test creating an inactive template"""
        template = NotificationTemplate(
            event_type="OLD_EVENT",
            notification_type=NotificationType.EMAIL.value,
            subject_template="Old template",
            body_template="This template is inactive",
            is_active=0,
            priority=NotificationPriority.LOW.value
        )

        db_session.add(template)
        db_session.commit()

        # Query only active templates
        active_templates = db_session.query(NotificationTemplate).filter_by(
            event_type="OLD_EVENT",
            is_active=1
        ).all()

        assert len(active_templates) == 0

    def test_create_user_notification_preference(self, db_session, sample_user_id):
        """Test creating user notification preferences"""
        preference = UserNotificationPreference(
            user_id=sample_user_id,
            email_enabled=1,
            push_enabled=1,
            fcm_token="sample-fcm-token",
            reservation_notifications=1,
            payment_notifications=1,
            marketing_notifications=0
        )

        db_session.add(preference)
        db_session.commit()
        db_session.refresh(preference)

        assert preference.id is not None
        assert preference.user_id == sample_user_id
        assert preference.email_enabled == 1
        assert preference.push_enabled == 1
        assert preference.fcm_token == "sample-fcm-token"
        assert preference.reservation_notifications == 1
        assert preference.payment_notifications == 1
        assert preference.marketing_notifications == 0
        assert preference.created_at is not None

    def test_user_preference_update_fcm_token(self, db_session, sample_user_preference):
        """Test updating user FCM token"""
        old_token = sample_user_preference.fcm_token
        new_token = "new-fcm-token-456"

        sample_user_preference.fcm_token = new_token
        db_session.commit()

        # Verify update
        retrieved = db_session.query(UserNotificationPreference).filter_by(
            id=sample_user_preference.id
        ).first()

        assert retrieved.fcm_token == new_token
        assert retrieved.fcm_token != old_token

    def test_user_preference_disable_notifications(self, db_session, sample_user_preference):
        """Test disabling email and push notifications"""
        sample_user_preference.email_enabled = 0
        sample_user_preference.push_enabled = 0
        db_session.commit()

        retrieved = db_session.query(UserNotificationPreference).filter_by(
            id=sample_user_preference.id
        ).first()

        assert retrieved.email_enabled == 0
        assert retrieved.push_enabled == 0

    def test_user_preference_event_specific_settings(self, db_session, sample_user_id):
        """Test event-specific notification preferences using JSON"""
        event_preferences = {
            "RESERVATION_CONFIRMED": {
                "email": True,
                "push": True
            },
            "PAYMENT_SUCCESS": {
                "email": True,
                "push": False
            },
            "MARKETING": {
                "email": False,
                "push": False
            }
        }

        preference = UserNotificationPreference(
            user_id=sample_user_id,
            email_enabled=1,
            push_enabled=1,
            event_preferences=event_preferences
        )

        db_session.add(preference)
        db_session.commit()
        db_session.refresh(preference)

        assert preference.event_preferences is not None
        assert "RESERVATION_CONFIRMED" in preference.event_preferences
        assert preference.event_preferences["PAYMENT_SUCCESS"]["push"] is False

    def test_notification_with_json_data(self, db_session, sample_user_id):
        """Test notification with complex JSON data"""
        complex_data = {
            "reservation_id": "RES-12345",
            "parking_info": {
                "name": "Downtown Parking",
                "address": "123 Main St",
                "spot_number": "A-42"
            },
            "pricing": {
                "base_price": 10.00,
                "tax": 1.50,
                "total": 11.50
            }
        }

        notification = Notification(
            user_id=sample_user_id,
            notification_type=NotificationType.EMAIL.value,
            event_type="RESERVATION_CONFIRMED",
            recipient_email="test@example.com",
            subject="Complex Data Test",
            body="Test body",
            status=NotificationStatus.PENDING.value,
            priority=NotificationPriority.NORMAL.value,
            data=complex_data
        )

        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        assert notification.data is not None
        assert notification.data["reservation_id"] == "RES-12345"
        assert notification.data["parking_info"]["spot_number"] == "A-42"
        assert notification.data["pricing"]["total"] == 11.50

    def test_query_notifications_by_status(self, db_session, sample_user_id):
        """Test querying notifications by status"""
        # Create notifications with different statuses
        statuses = [
            NotificationStatus.PENDING,
            NotificationStatus.SENT,
            NotificationStatus.FAILED,
            NotificationStatus.RETRYING
        ]

        for status in statuses:
            notification = Notification(
                user_id=sample_user_id,
                notification_type=NotificationType.EMAIL.value,
                event_type="TEST_EVENT",
                recipient_email="test@example.com",
                subject="Test",
                body="Body",
                status=status.value,
                priority=NotificationPriority.NORMAL.value
            )
            db_session.add(notification)

        db_session.commit()

        # Query pending notifications
        pending = db_session.query(Notification).filter_by(
            status=NotificationStatus.PENDING.value
        ).all()

        assert len(pending) >= 1

    def test_query_notifications_by_user(self, db_session):
        """Test querying notifications by user ID"""
        user1 = str(uuid4())
        user2 = str(uuid4())

        # Create notifications for two different users
        for user_id in [user1, user2]:
            for i in range(3):
                notification = Notification(
                    user_id=user_id,
                    notification_type=NotificationType.EMAIL.value,
                    event_type="TEST_EVENT",
                    recipient_email=f"{user_id}@example.com",
                    subject="Test",
                    body="Body",
                    status=NotificationStatus.SENT.value,
                    priority=NotificationPriority.NORMAL.value
                )
                db_session.add(notification)

        db_session.commit()

        # Query notifications for user1
        user1_notifications = db_session.query(Notification).filter_by(
            user_id=user1
        ).all()

        assert len(user1_notifications) == 3
        assert all(n.user_id == user1 for n in user1_notifications)
