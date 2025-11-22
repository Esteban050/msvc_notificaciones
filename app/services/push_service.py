import firebase_admin
from firebase_admin import credentials, messaging
import logging
import os
from typing import Optional, Dict, Any
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PushNotificationService:
    def __init__(self):
        self.app = None
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Check if credentials file exists
                if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    self.app = firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin SDK initialized successfully")
                else:
                    logger.warning(
                        f"Firebase credentials file not found at {settings.FIREBASE_CREDENTIALS_PATH}. "
                        "Push notifications will not work until you provide valid credentials."
                    )
            else:
                self.app = firebase_admin.get_app()
                logger.info("Using existing Firebase app instance")

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            self.app = None

    async def send_push_notification(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a push notification using Firebase Cloud Messaging

        Args:
            fcm_token: Firebase Cloud Messaging token of the recipient device
            title: Notification title
            body: Notification body
            data: Additional data to send with the notification

        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.app:
            logger.error("Firebase not initialized. Cannot send push notification.")
            return False

        try:
            # Prepare notification payload
            notification = messaging.Notification(
                title=title,
                body=body
            )

            # Prepare data payload (convert all values to strings)
            data_payload = {}
            if data:
                for key, value in data.items():
                    data_payload[key] = str(value)

            # Create message
            message = messaging.Message(
                notification=notification,
                data=data_payload,
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        priority='high'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )

            # Send message
            response = messaging.send(message)
            logger.info(f"Push notification sent successfully: {response}")
            return True

        except messaging.UnregisteredError:
            logger.warning(f"FCM token is invalid or unregistered: {fcm_token}")
            return False
        except Exception as e:
            logger.error(f"Failed to send push notification: {str(e)}")
            return False

    async def send_push_notification_multicast(
        self,
        fcm_tokens: list[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple devices

        Args:
            fcm_tokens: List of FCM tokens
            title: Notification title
            body: Notification body
            data: Additional data

        Returns:
            dict: Response with success and failure counts
        """
        if not self.app:
            logger.error("Firebase not initialized. Cannot send push notifications.")
            return {"success_count": 0, "failure_count": len(fcm_tokens)}

        try:
            # Prepare data payload
            data_payload = {}
            if data:
                for key, value in data.items():
                    data_payload[key] = str(value)

            # Create multicast message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data=data_payload,
                tokens=fcm_tokens
            )

            # Send message
            response = messaging.send_multicast(message)
            logger.info(
                f"Push notifications sent: {response.success_count} successful, "
                f"{response.failure_count} failed"
            )

            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count
            }

        except Exception as e:
            logger.error(f"Failed to send multicast push notification: {str(e)}")
            return {"success_count": 0, "failure_count": len(fcm_tokens)}


# Singleton instance
push_service = PushNotificationService()
