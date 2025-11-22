import pika
import json
import logging
from typing import Callable
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQService:
    def __init__(self):
        self.host = settings.RABBITMQ_HOST
        self.port = settings.RABBITMQ_PORT
        self.user = settings.RABBITMQ_USER
        self.password = settings.RABBITMQ_PASSWORD
        self.queue_name = settings.RABBITMQ_QUEUE_NAME
        self.exchange_name = settings.RABBITMQ_EXCHANGE_NAME
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ (supports CloudAMQP)"""
        try:
            # Prioridad 1: Usar URL de CloudAMQP si está disponible
            if settings.RABBITMQ_URL:
                logger.info(f"Connecting to CloudAMQP using URL...")
                parameters = pika.URLParameters(settings.RABBITMQ_URL)
                # Configurar timeouts para CloudAMQP
                parameters.heartbeat = 600
                parameters.blocked_connection_timeout = 300
            else:
                # Prioridad 2: Usar configuración local individual
                logger.info(f"Connecting to RabbitMQ at {self.host}:{self.port}")
                credentials = pika.PlainCredentials(self.user, self.password)
                parameters = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='topic',
                durable=True
            )

            # Declare queue
            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True
            )

            # Bind queue to exchange with routing keys
            routing_keys = [
                # Authentication events
                'email.verification',
                'email.welcome',
                'email.password_reset',
                'email.password_changed',
                # Reservation events
                'reservation.created',
                'reservation.confirmed',
                'reservation.cancelled',
                'reservation.reminder',
                # Payment events
                'payment.success',
                'payment.failed',
                # Parking events
                'parking.spot.released'
            ]

            for routing_key in routing_keys:
                self.channel.queue_bind(
                    exchange=self.exchange_name,
                    queue=self.queue_name,
                    routing_key=routing_key
                )

            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            logger.info(f"Queue '{self.queue_name}' bound to exchange '{self.exchange_name}'")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    def consume(self, callback: Callable):
        """Start consuming messages from the queue"""
        if not self.channel:
            self.connect()

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=callback,
            auto_ack=False
        )

        logger.info(f"Waiting for messages in queue '{self.queue_name}'...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.channel.stop_consuming()
        finally:
            self.close()

    def publish(self, routing_key: str, message: dict):
        """Publish a message to the exchange"""
        if not self.channel:
            self.connect()

        try:
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            logger.info(f"Published message to {routing_key}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            raise

    def close(self):
        """Close the connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")


# Singleton instance
rabbitmq_service = RabbitMQService()
