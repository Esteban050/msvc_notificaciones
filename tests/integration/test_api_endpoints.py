"""
Integration tests for API endpoints
"""
import pytest
from uuid import uuid4

from app.models.notification import (
    Notification,
    NotificationTemplate,
    UserNotificationPreference,
    NotificationType,
    NotificationStatus,
    NotificationPriority
)


@pytest.mark.integration
class TestNotificationEndpoints:
    """Integration tests for notification endpoints"""

    def test_get_all_notifications(self, client, db_session, sample_notification):
        """Test GET /notifications - retrieve all notifications"""
        response = client.get("/notifications")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    def test_get_notifications_with_filters(self, client, db_session, sample_user_id):
        """Test GET /notifications with user_id filter"""
        # Create multiple notifications
        for i in range(3):
            notification = Notification(
                user_id=sample_user_id,
                notification_type=NotificationType.EMAIL.value,
                event_type="TEST_EVENT",
                recipient_email=f"test{i}@example.com",
                subject=f"Test {i}",
                body="Test body",
                status=NotificationStatus.SENT.value,
                priority=NotificationPriority.NORMAL.value
            )
            db_session.add(notification)
        db_session.commit()

        response = client.get(f"/notifications?user_id={sample_user_id}")

        assert response.status_code == 200
        notifications = response.json()
        assert len(notifications) >= 3
        assert all(n["user_id"] == sample_user_id for n in notifications)

    def test_get_notifications_with_status_filter(self, client, db_session, sample_user_id):
        """Test GET /notifications with status filter"""
        # Create notifications with different statuses
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

        response = client.get(f"/notifications?status={NotificationStatus.PENDING.value}")

        assert response.status_code == 200
        notifications = response.json()
        assert len(notifications) > 0
        assert all(n["status"] == NotificationStatus.PENDING.value for n in notifications)

    def test_get_notification_by_id(self, client, db_session, sample_notification):
        """Test GET /notifications/{notification_id}"""
        response = client.get(f"/notifications/{sample_notification.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_notification.id)
        assert data["event_type"] == sample_notification.event_type

    def test_get_notification_by_id_not_found(self, client):
        """Test GET /notifications/{notification_id} - not found"""
        fake_id = str(uuid4())
        response = client.get(f"/notifications/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_user_notifications(self, client, db_session, sample_user_id):
        """Test GET /notifications/user/{user_id}"""
        # Create notifications for the user
        for i in range(5):
            notification = Notification(
                user_id=sample_user_id,
                notification_type=NotificationType.EMAIL.value,
                event_type="TEST_EVENT",
                recipient_email="test@example.com",
                subject=f"Test {i}",
                body="Body",
                status=NotificationStatus.SENT.value,
                priority=NotificationPriority.NORMAL.value
            )
            db_session.add(notification)
        db_session.commit()

        response = client.get(f"/notifications/user/{sample_user_id}")

        assert response.status_code == 200
        notifications = response.json()
        assert len(notifications) >= 5
        assert all(n["user_id"] == sample_user_id for n in notifications)

    def test_get_user_notifications_pagination(self, client, db_session, sample_user_id):
        """Test GET /notifications/user/{user_id} with pagination"""
        # Create 10 notifications
        for i in range(10):
            notification = Notification(
                user_id=sample_user_id,
                notification_type=NotificationType.EMAIL.value,
                event_type="TEST_EVENT",
                recipient_email="test@example.com",
                subject=f"Test {i}",
                body="Body",
                status=NotificationStatus.SENT.value,
                priority=NotificationPriority.NORMAL.value
            )
            db_session.add(notification)
        db_session.commit()

        # Get first page (limit 5)
        response = client.get(f"/notifications/user/{sample_user_id}?skip=0&limit=5")

        assert response.status_code == 200
        assert len(response.json()) == 5


@pytest.mark.integration
class TestTemplateEndpoints:
    """Integration tests for template endpoints"""

    def test_get_all_templates(self, client, db_session, sample_notification_template):
        """Test GET /templates"""
        response = client.get("/templates")

        assert response.status_code == 200
        templates = response.json()
        assert isinstance(templates, list)
        assert len(templates) > 0

    def test_get_templates_by_event_type(self, client, db_session, sample_notification_template):
        """Test GET /templates/{event_type}"""
        response = client.get("/templates/RESERVATION_CONFIRMED")

        assert response.status_code == 200
        templates = response.json()
        assert len(templates) > 0
        assert all(t["event_type"] == "RESERVATION_CONFIRMED" for t in templates)

    def test_get_templates_by_event_type_not_found(self, client):
        """Test GET /templates/{event_type} - not found"""
        response = client.get("/templates/NON_EXISTENT_EVENT")

        assert response.status_code == 404

    def test_create_template(self, client, db_session):
        """Test POST /templates - create new template"""
        template_data = {
            "event_type": "NEW_EVENT",
            "notification_type": "EMAIL",
            "subject_template": "New Event: {name}",
            "body_template": "This is a new event for {name}",
            "priority": "NORMAL",
            "is_active": True
        }

        response = client.post("/templates", json=template_data)

        assert response.status_code == 201
        data = response.json()
        assert data["event_type"] == "NEW_EVENT"
        assert data["notification_type"] == "EMAIL"
        assert data["subject_template"] == "New Event: {name}"
        assert data["is_active"] == 1

    def test_create_template_duplicate(self, client, db_session, sample_notification_template):
        """Test POST /templates - duplicate template"""
        template_data = {
            "event_type": sample_notification_template.event_type,
            "notification_type": sample_notification_template.notification_type.value,
            "subject_template": "Duplicate",
            "body_template": "Duplicate body",
            "priority": "NORMAL",
            "is_active": True
        }

        response = client.post("/templates", json=template_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_update_template(self, client, db_session, sample_notification_template):
        """Test PUT /templates/{template_id}"""
        update_data = {
            "subject_template": "Updated Subject: {parking_name}",
            "body_template": "Updated body content",
            "is_active": False
        }

        response = client.put(
            f"/templates/{sample_notification_template.id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["subject_template"] == "Updated Subject: {parking_name}"
        assert data["body_template"] == "Updated body content"
        assert data["is_active"] == 0

    def test_update_template_not_found(self, client):
        """Test PUT /templates/{template_id} - not found"""
        fake_id = str(uuid4())
        update_data = {"subject_template": "Updated"}

        response = client.put(f"/templates/{fake_id}", json=update_data)

        assert response.status_code == 404

    def test_delete_template(self, client, db_session):
        """Test DELETE /templates/{template_id}"""
        # Create a template to delete
        template = NotificationTemplate(
            event_type="DELETE_TEST",
            notification_type=NotificationType.EMAIL.value,
            subject_template="Test",
            body_template="Test body",
            is_active=1,
            priority=NotificationPriority.NORMAL.value
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        response = client.delete(f"/templates/{template.id}")

        assert response.status_code == 204

        # Verify deletion
        deleted = db_session.query(NotificationTemplate).filter_by(id=template.id).first()
        assert deleted is None

    def test_delete_template_not_found(self, client):
        """Test DELETE /templates/{template_id} - not found"""
        fake_id = str(uuid4())
        response = client.delete(f"/templates/{fake_id}")

        assert response.status_code == 404


@pytest.mark.integration
class TestUserPreferenceEndpoints:
    """Integration tests for user preference endpoints"""

    def test_get_user_preferences(self, client, db_session, sample_user_preference):
        """Test GET /preferences/{user_id}"""
        response = client.get(f"/preferences/{sample_user_preference.user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(sample_user_preference.user_id)
        assert data["email_enabled"] == 1
        assert data["push_enabled"] == 1

    def test_get_user_preferences_not_found(self, client):
        """Test GET /preferences/{user_id} - not found"""
        fake_id = str(uuid4())
        response = client.get(f"/preferences/{fake_id}")

        assert response.status_code == 404

    def test_create_user_preferences(self, client, db_session):
        """Test POST /preferences - create new preferences"""
        user_id = str(uuid4())
        preference_data = {
            "user_id": user_id,
            "email_enabled": True,
            "push_enabled": True,
            "fcm_token": "test-fcm-token",
            "event_preferences": {
                "RESERVATION_CONFIRMED": {
                    "email": True,
                    "push": True
                }
            }
        }

        response = client.post("/preferences", json=preference_data)

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user_id
        assert data["email_enabled"] == 1
        assert data["push_enabled"] == 1
        assert data["fcm_token"] == "test-fcm-token"

    def test_create_user_preferences_duplicate(self, client, db_session, sample_user_preference):
        """Test POST /preferences - duplicate preferences"""
        preference_data = {
            "user_id": str(sample_user_preference.user_id),
            "email_enabled": True,
            "push_enabled": True
        }

        response = client.post("/preferences", json=preference_data)

        assert response.status_code == 400
        assert "already exist" in response.json()["detail"].lower()

    def test_update_user_preferences(self, client, db_session, sample_user_preference):
        """Test PUT /preferences/{user_id}"""
        update_data = {
            "email_enabled": False,
            "push_enabled": True,
            "fcm_token": "updated-fcm-token"
        }

        response = client.put(
            f"/preferences/{sample_user_preference.user_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email_enabled"] == 0
        assert data["push_enabled"] == 1
        assert data["fcm_token"] == "updated-fcm-token"

    def test_update_user_preferences_not_found(self, client):
        """Test PUT /preferences/{user_id} - not found"""
        fake_id = str(uuid4())
        update_data = {"email_enabled": False}

        response = client.put(f"/preferences/{fake_id}", json=update_data)

        assert response.status_code == 404

    def test_update_fcm_token_existing_user(self, client, db_session, sample_user_preference):
        """Test PUT /preferences/{user_id}/fcm-token - existing user"""
        new_token = "new-fcm-token-789"

        response = client.put(
            f"/preferences/{sample_user_preference.user_id}/fcm-token",
            params={"fcm_token": new_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "FCM token updated successfully"
        assert data["user_id"] == str(sample_user_preference.user_id)

        # Verify in database
        updated = db_session.query(UserNotificationPreference).filter_by(
            user_id=sample_user_preference.user_id
        ).first()
        assert updated.fcm_token == new_token

    def test_update_fcm_token_new_user(self, client, db_session):
        """Test PUT /preferences/{user_id}/fcm-token - new user (auto-create)"""
        new_user_id = str(uuid4())
        fcm_token = "auto-created-token"

        response = client.put(
            f"/preferences/{new_user_id}/fcm-token",
            params={"fcm_token": fcm_token}
        )

        assert response.status_code == 200

        # Verify preferences were created
        created = db_session.query(UserNotificationPreference).filter_by(
            user_id=new_user_id
        ).first()
        assert created is not None
        assert created.fcm_token == fcm_token
        assert created.email_enabled == 1
        assert created.push_enabled == 1


@pytest.mark.integration
class TestHealthCheckEndpoint:
    """Integration tests for health check endpoint"""

    def test_health_check(self, client):
        """Test GET /health"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "notifications"
