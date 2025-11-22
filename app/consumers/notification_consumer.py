import json
import logging
import sys
import os
from pathlib import Path
from uuid import UUID

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.rabbitmq_service import rabbitmq_service
from app.services.notification_service import notification_service
from app.schemas.notification import NotificationEvent
from pydantic import ValidationError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def map_routing_key_to_event_type(routing_key: str) -> str:
    """
    Map RabbitMQ routing key to internal event type
    """
    routing_key_mapping = {
        # Authentication events
        'email.verification': 'EMAIL_VERIFICATION',
        'email.welcome': 'EMAIL_WELCOME',
        'email.password_reset': 'EMAIL_PASSWORD_RESET',
        'email.password_changed': 'EMAIL_PASSWORD_CHANGED',
        # Reservation events
        'reservation.created': 'RESERVATION_CREATED',
        'reservation.confirmed': 'RESERVATION_CONFIRMED',
        'reservation.cancelled': 'RESERVATION_CANCELLED',
        'reservation.reminder': 'RESERVATION_REMINDER',
        # Payment events
        'payment.success': 'PAYMENT_SUCCESS',
        'payment.failed': 'PAYMENT_FAILED',
        # Parking events
        'parking.spot.released': 'SPOT_RELEASED'
    }

    return routing_key_mapping.get(routing_key, routing_key.upper().replace('.', '_'))


def transform_auth_event(message: dict, event_type: str, routing_key: str) -> dict:
    """
    Transform authentication service event format to internal NotificationEvent format
    Handles both auth service format (user_id as int) and internal format (UUID)
    """
    # Check if this is an auth event (email.* routing key)
    if routing_key.startswith('email.'):
        # Auth service format
        user_id = message.get('user_id')

        # Convert integer user_id to UUID (using UUID version 5 with namespace)
        # This creates deterministic UUIDs from integer IDs
        from uuid import uuid5, NAMESPACE_DNS
        if isinstance(user_id, int):
            user_id = str(uuid5(NAMESPACE_DNS, f"user-{user_id}"))

        # Build verification/reset links if tokens are present
        data = {}
        frontend_url = message.get('frontend_url', 'http://localhost:3000')

        if 'verification_token' in message:
            data['verification_link'] = f"{frontend_url}/verify-email?token={message['verification_token']}"
            data['verification_token'] = message['verification_token']

        if 'reset_token' in message:
            data['reset_link'] = f"{frontend_url}/reset-password?token={message['reset_token']}"
            data['reset_token'] = message['reset_token']

        # Include all other fields
        data['name'] = message.get('name', '')
        data['email'] = message.get('email', '')
        data['frontend_url'] = frontend_url

        return {
            'user_id': user_id,
            'user_email': message.get('email'),
            'event_type': event_type,
            'data': data,
            'priority': 'normal'
        }
    else:
        # Already in internal format or other service format
        if 'event_type' not in message:
            message['event_type'] = event_type
        return message


def process_notification_event(ch, method, properties, body):
    """
    Callback function to process notification events from RabbitMQ
    """
    try:
        # Parse the message
        message = json.loads(body)
        routing_key = method.routing_key
        logger.info(f"Received notification event with routing key '{routing_key}': {message}")

        # Map routing key to event type
        event_type = map_routing_key_to_event_type(routing_key)

        # Transform auth service message format to internal format
        transformed_message = transform_auth_event(message, event_type, routing_key)

        # Validate the event using Pydantic schema
        event = NotificationEvent(**transformed_message)

        # Process the notification
        notification_service.process_event(event)

        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Successfully processed event: {event.event_type} for user {event.user_id}")

    except ValidationError as e:
        logger.error(f"Invalid event format: {str(e)}")
        # Reject and don't requeue invalid messages
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

    except Exception as e:
        logger.error(f"Error processing notification event: {str(e)}")
        # Reject and requeue for retry
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def main():
    """
    Main function to start the notification consumer
    """
    logger.info("Starting Notification Consumer...")

    try:
        # Connect to RabbitMQ
        rabbitmq_service.connect()

        # Start consuming messages
        rabbitmq_service.consume(process_notification_event)

    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
    except Exception as e:
        logger.error(f"Consumer error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
