"""
Unit tests for push_service.py
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from firebase_admin import messaging

from app.services.push_service import PushNotificationService


@pytest.mark.unit
class TestPushNotificationService:
    """Test suite for PushNotificationService"""

    @pytest.fixture
    def push_service_instance(self):
        """Create a fresh PushNotificationService instance for testing"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase:
            mock_firebase._apps = {}
            service = PushNotificationService()
            return service

    def test_initialize_firebase_success(self):
        """Test successful Firebase initialization"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.credentials') as mock_creds, \
             patch('app.services.push_service.os.path.exists', return_value=True):

            mock_firebase._apps = {}
            mock_app = MagicMock()
            mock_firebase.initialize_app.return_value = mock_app

            service = PushNotificationService()

            assert service.app is not None
            mock_firebase.initialize_app.assert_called_once()

    def test_initialize_firebase_credentials_not_found(self):
        """Test Firebase initialization when credentials file doesn't exist"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.os.path.exists', return_value=False):

            mock_firebase._apps = {}

            service = PushNotificationService()

            # Service should initialize but app should be None
            assert service.app is None

    def test_initialize_firebase_already_initialized(self):
        """Test Firebase initialization when already initialized"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase:

            existing_app = MagicMock()
            mock_firebase._apps = {'default': existing_app}
            mock_firebase.get_app.return_value = existing_app

            service = PushNotificationService()

            assert service.app == existing_app
            mock_firebase.get_app.assert_called_once()

    def test_initialize_firebase_exception(self):
        """Test Firebase initialization exception handling"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.os.path.exists', return_value=True), \
             patch('app.services.push_service.credentials') as mock_creds:

            mock_firebase._apps = {}
            mock_firebase.initialize_app.side_effect = Exception("Firebase init failed")

            service = PushNotificationService()

            assert service.app is None

    @pytest.mark.asyncio
    async def test_send_push_notification_success(self):
        """Test successful push notification sending"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.messaging') as mock_messaging, \
             patch('app.services.push_service.os.path.exists', return_value=True):

            mock_firebase._apps = {}
            mock_app = MagicMock()
            mock_firebase.initialize_app.return_value = mock_app

            mock_messaging.send.return_value = "message-id-123"

            service = PushNotificationService()

            result = await service.send_push_notification(
                fcm_token="test-fcm-token",
                title="Test Title",
                body="Test Body",
                data={"key": "value"}
            )

            assert result is True
            mock_messaging.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_push_notification_firebase_not_initialized(self):
        """Test push notification when Firebase is not initialized"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase:
            mock_firebase._apps = {}

            service = PushNotificationService()
            service.app = None

            result = await service.send_push_notification(
                fcm_token="test-token",
                title="Title",
                body="Body"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_push_notification_invalid_token(self):
        """Test push notification with invalid/unregistered FCM token"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.messaging') as mock_messaging, \
             patch('app.services.push_service.os.path.exists', return_value=True):

            mock_firebase._apps = {}
            mock_app = MagicMock()
            mock_firebase.initialize_app.return_value = mock_app

            # Simulate UnregisteredError
            mock_messaging.send.side_effect = messaging.UnregisteredError("Token unregistered")
            mock_messaging.UnregisteredError = messaging.UnregisteredError

            service = PushNotificationService()

            result = await service.send_push_notification(
                fcm_token="invalid-token",
                title="Title",
                body="Body"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_push_notification_general_exception(self):
        """Test push notification with general exception"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.messaging') as mock_messaging, \
             patch('app.services.push_service.os.path.exists', return_value=True):

            mock_firebase._apps = {}
            mock_app = MagicMock()
            mock_firebase.initialize_app.return_value = mock_app

            mock_messaging.send.side_effect = Exception("Network error")

            service = PushNotificationService()

            result = await service.send_push_notification(
                fcm_token="test-token",
                title="Title",
                body="Body"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_push_notification_with_data(self):
        """Test push notification with additional data payload"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.messaging') as mock_messaging, \
             patch('app.services.push_service.os.path.exists', return_value=True):

            mock_firebase._apps = {}
            mock_app = MagicMock()
            mock_firebase.initialize_app.return_value = mock_app

            mock_messaging.send.return_value = "message-id"
            mock_messaging.Message = messaging.Message
            mock_messaging.Notification = messaging.Notification
            mock_messaging.AndroidConfig = messaging.AndroidConfig
            mock_messaging.APNSConfig = messaging.APNSConfig

            service = PushNotificationService()

            data = {
                "reservation_id": "RES-123",
                "price": 15.50,
                "parking_name": "Downtown"
            }

            result = await service.send_push_notification(
                fcm_token="test-token",
                title="Reservation Confirmed",
                body="Your reservation is confirmed",
                data=data
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_push_notification_without_data(self):
        """Test push notification without additional data"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.messaging') as mock_messaging, \
             patch('app.services.push_service.os.path.exists', return_value=True):

            mock_firebase._apps = {}
            mock_app = MagicMock()
            mock_firebase.initialize_app.return_value = mock_app

            mock_messaging.send.return_value = "message-id"

            service = PushNotificationService()

            result = await service.send_push_notification(
                fcm_token="test-token",
                title="Simple Notification",
                body="This is a simple notification"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_push_notification_multicast_success(self):
        """Test successful multicast push notification"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.messaging') as mock_messaging, \
             patch('app.services.push_service.os.path.exists', return_value=True):

            mock_firebase._apps = {}
            mock_app = MagicMock()
            mock_firebase.initialize_app.return_value = mock_app

            # Mock multicast response
            mock_response = MagicMock()
            mock_response.success_count = 3
            mock_response.failure_count = 0
            mock_messaging.send_multicast.return_value = mock_response

            service = PushNotificationService()

            tokens = ["token1", "token2", "token3"]
            result = await service.send_push_notification_multicast(
                fcm_tokens=tokens,
                title="Multicast Test",
                body="Testing multicast",
                data={"event": "test"}
            )

            assert result["success_count"] == 3
            assert result["failure_count"] == 0
            mock_messaging.send_multicast.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_push_notification_multicast_partial_failure(self):
        """Test multicast push notification with partial failures"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.messaging') as mock_messaging, \
             patch('app.services.push_service.os.path.exists', return_value=True):

            mock_firebase._apps = {}
            mock_app = MagicMock()
            mock_firebase.initialize_app.return_value = mock_app

            mock_response = MagicMock()
            mock_response.success_count = 2
            mock_response.failure_count = 1
            mock_messaging.send_multicast.return_value = mock_response

            service = PushNotificationService()

            tokens = ["token1", "invalid-token", "token3"]
            result = await service.send_push_notification_multicast(
                fcm_tokens=tokens,
                title="Test",
                body="Body"
            )

            assert result["success_count"] == 2
            assert result["failure_count"] == 1

    @pytest.mark.asyncio
    async def test_send_push_notification_multicast_firebase_not_initialized(self):
        """Test multicast when Firebase is not initialized"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase:
            mock_firebase._apps = {}

            service = PushNotificationService()
            service.app = None

            tokens = ["token1", "token2"]
            result = await service.send_push_notification_multicast(
                fcm_tokens=tokens,
                title="Test",
                body="Body"
            )

            assert result["success_count"] == 0
            assert result["failure_count"] == 2

    @pytest.mark.asyncio
    async def test_send_push_notification_multicast_exception(self):
        """Test multicast exception handling"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.messaging') as mock_messaging, \
             patch('app.services.push_service.os.path.exists', return_value=True):

            mock_firebase._apps = {}
            mock_app = MagicMock()
            mock_firebase.initialize_app.return_value = mock_app

            mock_messaging.send_multicast.side_effect = Exception("Network error")

            service = PushNotificationService()

            tokens = ["token1", "token2"]
            result = await service.send_push_notification_multicast(
                fcm_tokens=tokens,
                title="Test",
                body="Body"
            )

            assert result["success_count"] == 0
            assert result["failure_count"] == 2

    @pytest.mark.asyncio
    async def test_send_push_notification_data_conversion_to_string(self):
        """Test that data values are converted to strings"""
        with patch('app.services.push_service.firebase_admin') as mock_firebase, \
             patch('app.services.push_service.messaging') as mock_messaging, \
             patch('app.services.push_service.os.path.exists', return_value=True):

            mock_firebase._apps = {}
            mock_app = MagicMock()
            mock_firebase.initialize_app.return_value = mock_app

            mock_messaging.send.return_value = "message-id"

            service = PushNotificationService()

            # Data with various types (int, float, bool)
            data = {
                "count": 42,
                "price": 15.99,
                "active": True
            }

            result = await service.send_push_notification(
                fcm_token="test-token",
                title="Test",
                body="Body",
                data=data
            )

            assert result is True
            # All data values should be converted to strings internally
