import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.notification import (
    Notification,
    NotificationTemplate,
    UserNotificationPreference,
    NotificationType,
    NotificationStatus,
    NotificationPriority
)
from app.schemas.notification import NotificationEvent, NotificationCreate
from app.services.email_service import email_service
from app.services.push_service import push_service
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.max_retries = settings.MAX_RETRY_ATTEMPTS
        self.retry_delay = settings.RETRY_DELAY_SECONDS

    def process_event(self, event: NotificationEvent):
        """
        Process a notification event from the message queue
        """
        db = SessionLocal()
        try:
            # Get user preferences
            preferences = self._get_user_preferences(db, event.user_id)

            # Get templates for this event type
            templates = self._get_templates(db, event.event_type)

            # Determine which notifications to send based on preferences
            notifications_to_send = []

            for template in templates:
                # Check if user wants this type of notification
                if not self._should_send_notification(preferences, template, event.event_type):
                    logger.info(
                        f"Skipping {template.notification_type} for user {event.user_id} "
                        f"based on preferences"
                    )
                    continue

                # Render template with event data
                rendered = self._render_template(template, event.data)

                # Create notification record
                if template.notification_type == NotificationType.EMAIL:
                    if event.user_email:
                        notification = self._create_notification(
                            db=db,
                            user_id=event.user_id,
                            notification_type=NotificationType.EMAIL,
                            event_type=event.event_type,
                            recipient_email=event.user_email,
                            subject=rendered['subject'],
                            body=rendered['body'],
                            data=event.data,
                            priority=template.priority
                        )
                        notifications_to_send.append(notification)
                    else:
                        logger.warning(f"No email provided for user {event.user_id}")

                elif template.notification_type == NotificationType.PUSH:
                    fcm_token = event.fcm_token or (preferences.fcm_token if preferences else None)
                    if fcm_token:
                        notification = self._create_notification(
                            db=db,
                            user_id=event.user_id,
                            notification_type=NotificationType.PUSH,
                            event_type=event.event_type,
                            recipient_fcm_token=fcm_token,
                            title=rendered['title'],
                            body=rendered['body'],
                            data=event.data,
                            priority=template.priority
                        )
                        notifications_to_send.append(notification)
                    else:
                        logger.warning(f"No FCM token found for user {event.user_id}")

            # Send all notifications
            for notification in notifications_to_send:
                asyncio.run(self._send_notification(db, notification))

        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")
        finally:
            db.close()

    def _get_user_preferences(
        self,
        db: Session,
        user_id: str
    ) -> Optional[UserNotificationPreference]:
        """Get user notification preferences"""
        return db.query(UserNotificationPreference).filter(
            UserNotificationPreference.user_id == user_id
        ).first()

    def _get_templates(self, db: Session, event_type: str) -> list[NotificationTemplate]:
        """Get active templates for an event type"""
        return db.query(NotificationTemplate).filter(
            NotificationTemplate.event_type == event_type,
            NotificationTemplate.is_active == 1
        ).all()

    def _should_send_notification(
        self,
        preferences: Optional[UserNotificationPreference],
        template: NotificationTemplate,
        event_type: str
    ) -> bool:
        """Determine if notification should be sent based on user preferences"""
        if not preferences:
            return True  # Send by default if no preferences set

        # Check global preferences
        if template.notification_type == NotificationType.EMAIL and not preferences.email_enabled:
            return False
        if template.notification_type == NotificationType.PUSH and not preferences.push_enabled:
            return False

        # Check event-specific preferences
        if preferences.event_preferences and event_type in preferences.event_preferences:
            event_pref = preferences.event_preferences[event_type]
            notification_type_key = template.notification_type.value
            if notification_type_key in event_pref:
                return event_pref[notification_type_key]

        return True

    def _render_template(self, template: NotificationTemplate, data: dict) -> dict:
        """Render notification template with event data"""
        rendered = {}

        # Simple template rendering (replace {key} with values)
        if template.subject_template:
            rendered['subject'] = self._replace_placeholders(template.subject_template, data)

        if template.title_template:
            rendered['title'] = self._replace_placeholders(template.title_template, data)

        rendered['body'] = self._replace_placeholders(template.body_template, data)

        return rendered

    def _replace_placeholders(self, template: str, data: dict) -> str:
        """Replace {key} placeholders in template with actual values"""
        result = template
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        return result

    def _create_notification(
        self,
        db: Session,
        user_id: str,
        notification_type: NotificationType,
        event_type: str,
        body: str,
        data: dict,
        priority: NotificationPriority,
        recipient_email: Optional[str] = None,
        recipient_fcm_token: Optional[str] = None,
        subject: Optional[str] = None,
        title: Optional[str] = None
    ) -> Notification:
        """Create a notification record in the database"""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            event_type=event_type,
            recipient_email=recipient_email,
            recipient_fcm_token=recipient_fcm_token,
            subject=subject,
            title=title,
            body=body,
            data=data,
            priority=priority,
            status=NotificationStatus.PENDING
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    async def _send_notification(self, db: Session, notification: Notification):
        """
        Send a notification via the appropriate channel.

        Estrategia híbrida:
        1. Si el usuario está conectado via WebSocket → enviar por WebSocket
        2. Si no está conectado → enviar por FCM (push) o Email
        """
        try:
            success = False
            sent_via_websocket = False

            # NUEVO: Intentar enviar via WebSocket primero si es notificación push
            if notification.notification_type == NotificationType.PUSH:
                from app.websockets.connection_manager import manager

                # Verificar si el usuario está conectado
                if manager.is_user_connected(str(notification.user_id)):
                    # Enviar via WebSocket
                    ws_notification = {
                        "id": str(notification.id),
                        "type": notification.notification_type.value,
                        "event_type": notification.event_type,
                        "title": notification.title,
                        "body": notification.body,
                        "data": notification.data,
                        "created_at": notification.created_at.isoformat(),
                        "priority": notification.priority.value
                    }

                    sent_via_websocket = await manager.send_notification(
                        user_id=str(notification.user_id),
                        notification=ws_notification
                    )

                    if sent_via_websocket:
                        success = True
                        logger.info(
                            f"Notification {notification.id} sent via WebSocket "
                            f"to user {notification.user_id}"
                        )

                # Si no se envió por WebSocket, enviar por FCM
                if not sent_via_websocket and notification.recipient_fcm_token:
                    success = await push_service.send_push_notification(
                        fcm_token=notification.recipient_fcm_token,
                        title=notification.title,
                        body=notification.body,
                        data=notification.data
                    )
                    if success:
                        logger.info(
                            f"Notification {notification.id} sent via FCM "
                            f"(user not connected via WebSocket)"
                        )

            elif notification.notification_type == NotificationType.EMAIL:
                # Email siempre se envía (no depende de WebSocket)
                html_body = email_service.generate_html_template(
                    title=notification.subject,
                    body=notification.body,
                    data=notification.data
                )
                success = await email_service.send_email(
                    to_email=notification.recipient_email,
                    subject=notification.subject,
                    body=html_body,
                    is_html=True
                )

            # Update notification status
            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                # Agregar metadata sobre el canal usado
                if not notification.data:
                    notification.data = {}
                notification.data['sent_via'] = 'websocket' if sent_via_websocket else notification.notification_type.value
                logger.info(f"Notification {notification.id} sent successfully")
            else:
                await self._handle_failed_notification(db, notification)

            db.commit()

        except Exception as e:
            logger.error(f"Error sending notification {notification.id}: {str(e)}")
            await self._handle_failed_notification(db, notification, str(e))
            db.commit()

    async def _handle_failed_notification(
        self,
        db: Session,
        notification: Notification,
        error_message: str = None
    ):
        """Handle failed notification with retry logic"""
        notification.retry_count += 1

        if notification.retry_count < notification.max_retries:
            notification.status = NotificationStatus.RETRYING
            notification.next_retry_at = datetime.utcnow() + timedelta(
                seconds=self.retry_delay * notification.retry_count
            )
            logger.warning(
                f"Notification {notification.id} failed. "
                f"Retry {notification.retry_count}/{notification.max_retries} "
                f"scheduled for {notification.next_retry_at}"
            )
        else:
            notification.status = NotificationStatus.FAILED
            logger.error(
                f"Notification {notification.id} failed after "
                f"{notification.max_retries} attempts"
            )

        if error_message:
            notification.error_message = error_message


# Singleton instance
notification_service = NotificationService()
