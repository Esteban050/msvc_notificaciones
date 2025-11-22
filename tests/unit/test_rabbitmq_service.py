"""
Unit tests for rabbitmq_service.py
"""
import pytest
import json
from unittest.mock import MagicMock, patch

from app.services.rabbitmq_service import RabbitMQService


@pytest.mark.unit
class TestRabbitMQService:
    """Test suite for RabbitMQService"""

    @pytest.fixture
    def rabbitmq_service_instance(self):
        """Create a fresh RabbitMQService instance for testing"""
        return RabbitMQService()

    def test_connect_with_url_cloudamqp(self, rabbitmq_service_instance, mock_rabbitmq):
        """Test connection using CloudAMQP URL"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika', mock_rabbitmq['pika']):

            mock_settings.RABBITMQ_URL = "amqps://user:pass@host.rmq.cloudamqp.com/vhost"
            mock_settings.RABBITMQ_EXCHANGE_NAME = "notifications_exchange"
            mock_settings.RABBITMQ_QUEUE_NAME = "notifications_queue"

            rabbitmq_service_instance.connect()

            # Verify URL parameters were used
            mock_rabbitmq['pika'].URLParameters.assert_called_once_with(
                "amqps://user:pass@host.rmq.cloudamqp.com/vhost"
            )

            # Verify connection was established
            assert rabbitmq_service_instance.connection is not None
            assert rabbitmq_service_instance.channel is not None

    def test_connect_with_local_credentials(self, rabbitmq_service_instance, mock_rabbitmq):
        """Test connection using local RabbitMQ credentials"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika', mock_rabbitmq['pika']):

            mock_settings.RABBITMQ_URL = None
            mock_settings.RABBITMQ_HOST = "localhost"
            mock_settings.RABBITMQ_PORT = 5672
            mock_settings.RABBITMQ_USER = "guest"
            mock_settings.RABBITMQ_PASSWORD = "guest"
            mock_settings.RABBITMQ_EXCHANGE_NAME = "test_exchange"
            mock_settings.RABBITMQ_QUEUE_NAME = "test_queue"

            rabbitmq_service_instance.host = "localhost"
            rabbitmq_service_instance.port = 5672
            rabbitmq_service_instance.user = "guest"
            rabbitmq_service_instance.password = "guest"
            rabbitmq_service_instance.exchange_name = "test_exchange"
            rabbitmq_service_instance.queue_name = "test_queue"

            rabbitmq_service_instance.connect()

            # Verify connection parameters were used
            mock_rabbitmq['pika'].ConnectionParameters.assert_called_once()
            assert rabbitmq_service_instance.connection is not None

    def test_connect_exchange_declaration(self, rabbitmq_service_instance, mock_rabbitmq):
        """Test that exchange is declared correctly"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika', mock_rabbitmq['pika']):

            mock_settings.RABBITMQ_URL = None
            mock_settings.RABBITMQ_HOST = "localhost"
            mock_settings.RABBITMQ_PORT = 5672
            mock_settings.RABBITMQ_USER = "guest"
            mock_settings.RABBITMQ_PASSWORD = "guest"
            mock_settings.RABBITMQ_EXCHANGE_NAME = "notifications_exchange"
            mock_settings.RABBITMQ_QUEUE_NAME = "notifications_queue"

            rabbitmq_service_instance.host = "localhost"
            rabbitmq_service_instance.exchange_name = "notifications_exchange"
            rabbitmq_service_instance.queue_name = "notifications_queue"

            rabbitmq_service_instance.connect()

            # Verify exchange declaration
            mock_rabbitmq['channel'].exchange_declare.assert_called_once_with(
                exchange="notifications_exchange",
                exchange_type='topic',
                durable=True
            )

    def test_connect_queue_declaration(self, rabbitmq_service_instance, mock_rabbitmq):
        """Test that queue is declared correctly"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika', mock_rabbitmq['pika']):

            mock_settings.RABBITMQ_URL = None
            mock_settings.RABBITMQ_HOST = "localhost"
            mock_settings.RABBITMQ_PORT = 5672
            mock_settings.RABBITMQ_USER = "guest"
            mock_settings.RABBITMQ_PASSWORD = "guest"
            mock_settings.RABBITMQ_EXCHANGE_NAME = "test_exchange"
            mock_settings.RABBITMQ_QUEUE_NAME = "test_queue"

            rabbitmq_service_instance.host = "localhost"
            rabbitmq_service_instance.exchange_name = "test_exchange"
            rabbitmq_service_instance.queue_name = "test_queue"

            rabbitmq_service_instance.connect()

            # Verify queue declaration
            mock_rabbitmq['channel'].queue_declare.assert_called_once_with(
                queue="test_queue",
                durable=True
            )

    def test_connect_queue_bindings(self, rabbitmq_service_instance, mock_rabbitmq):
        """Test that queue is bound to exchange with all routing keys"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika', mock_rabbitmq['pika']):

            mock_settings.RABBITMQ_URL = None
            mock_settings.RABBITMQ_HOST = "localhost"
            mock_settings.RABBITMQ_PORT = 5672
            mock_settings.RABBITMQ_USER = "guest"
            mock_settings.RABBITMQ_PASSWORD = "guest"
            mock_settings.RABBITMQ_EXCHANGE_NAME = "test_exchange"
            mock_settings.RABBITMQ_QUEUE_NAME = "test_queue"

            rabbitmq_service_instance.host = "localhost"
            rabbitmq_service_instance.exchange_name = "test_exchange"
            rabbitmq_service_instance.queue_name = "test_queue"

            rabbitmq_service_instance.connect()

            # Verify queue bindings (should be called multiple times)
            assert mock_rabbitmq['channel'].queue_bind.call_count > 0

            # Verify specific routing keys
            call_args_list = mock_rabbitmq['channel'].queue_bind.call_args_list
            routing_keys_bound = [call[1]['routing_key'] for call in call_args_list]

            expected_keys = [
                'email.verification',
                'reservation.confirmed',
                'payment.success'
            ]

            for key in expected_keys:
                assert key in routing_keys_bound

    def test_connect_connection_failure(self, rabbitmq_service_instance):
        """Test connection failure handling"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika') as mock_pika:

            mock_settings.RABBITMQ_URL = None
            mock_settings.RABBITMQ_HOST = "localhost"
            mock_settings.RABBITMQ_PORT = 5672
            mock_settings.RABBITMQ_USER = "guest"
            mock_settings.RABBITMQ_PASSWORD = "guest"

            rabbitmq_service_instance.host = "localhost"

            # Simulate connection error
            mock_pika.BlockingConnection.side_effect = Exception("Connection refused")

            with pytest.raises(Exception) as exc_info:
                rabbitmq_service_instance.connect()

            assert "Connection refused" in str(exc_info.value)

    def test_publish_message_success(self, rabbitmq_service_instance, mock_rabbitmq):
        """Test successful message publishing"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika', mock_rabbitmq['pika']):

            mock_settings.RABBITMQ_URL = None
            mock_settings.RABBITMQ_HOST = "localhost"
            mock_settings.RABBITMQ_PORT = 5672
            mock_settings.RABBITMQ_USER = "guest"
            mock_settings.RABBITMQ_PASSWORD = "guest"
            mock_settings.RABBITMQ_EXCHANGE_NAME = "test_exchange"
            mock_settings.RABBITMQ_QUEUE_NAME = "test_queue"

            rabbitmq_service_instance.host = "localhost"
            rabbitmq_service_instance.exchange_name = "test_exchange"
            rabbitmq_service_instance.queue_name = "test_queue"

            rabbitmq_service_instance.connect()

            message = {
                "user_id": "123",
                "event_type": "RESERVATION_CONFIRMED",
                "data": {"parking_name": "Test"}
            }

            rabbitmq_service_instance.publish(
                routing_key="reservation.confirmed",
                message=message
            )

            # Verify publish was called
            mock_rabbitmq['channel'].basic_publish.assert_called_once()

            # Verify message content
            call_args = mock_rabbitmq['channel'].basic_publish.call_args
            assert call_args[1]['routing_key'] == "reservation.confirmed"
            assert call_args[1]['exchange'] == "test_exchange"

            # Verify message body is JSON
            body = call_args[1]['body']
            parsed_body = json.loads(body)
            assert parsed_body == message

    def test_publish_message_with_persistence(self, rabbitmq_service_instance, mock_rabbitmq):
        """Test that published messages are persistent"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika', mock_rabbitmq['pika']):

            mock_settings.RABBITMQ_URL = None
            mock_settings.RABBITMQ_HOST = "localhost"
            mock_settings.RABBITMQ_PORT = 5672
            mock_settings.RABBITMQ_USER = "guest"
            mock_settings.RABBITMQ_PASSWORD = "guest"
            mock_settings.RABBITMQ_EXCHANGE_NAME = "test_exchange"
            mock_settings.RABBITMQ_QUEUE_NAME = "test_queue"

            rabbitmq_service_instance.host = "localhost"
            rabbitmq_service_instance.exchange_name = "test_exchange"
            rabbitmq_service_instance.queue_name = "test_queue"

            rabbitmq_service_instance.connect()

            message = {"test": "data"}
            rabbitmq_service_instance.publish("test.routing", message)

            # Verify properties include persistence (delivery_mode=2)
            call_args = mock_rabbitmq['channel'].basic_publish.call_args
            properties = call_args[1]['properties']
            assert properties.delivery_mode == 2
            assert properties.content_type == 'application/json'

    def test_publish_without_connection(self, rabbitmq_service_instance, mock_rabbitmq):
        """Test that publish auto-connects if no connection exists"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika', mock_rabbitmq['pika']):

            mock_settings.RABBITMQ_URL = None
            mock_settings.RABBITMQ_HOST = "localhost"
            mock_settings.RABBITMQ_PORT = 5672
            mock_settings.RABBITMQ_USER = "guest"
            mock_settings.RABBITMQ_PASSWORD = "guest"
            mock_settings.RABBITMQ_EXCHANGE_NAME = "test_exchange"
            mock_settings.RABBITMQ_QUEUE_NAME = "test_queue"

            rabbitmq_service_instance.host = "localhost"
            rabbitmq_service_instance.exchange_name = "test_exchange"
            rabbitmq_service_instance.queue_name = "test_queue"

            # Don't connect manually
            message = {"test": "data"}
            rabbitmq_service_instance.publish("test.key", message)

            # Verify connection was established automatically
            assert rabbitmq_service_instance.connection is not None

    def test_publish_failure(self, rabbitmq_service_instance, mock_rabbitmq):
        """Test publish failure handling"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika', mock_rabbitmq['pika']):

            mock_settings.RABBITMQ_URL = None
            mock_settings.RABBITMQ_HOST = "localhost"
            mock_settings.RABBITMQ_PORT = 5672
            mock_settings.RABBITMQ_USER = "guest"
            mock_settings.RABBITMQ_PASSWORD = "guest"
            mock_settings.RABBITMQ_EXCHANGE_NAME = "test_exchange"
            mock_settings.RABBITMQ_QUEUE_NAME = "test_queue"

            rabbitmq_service_instance.host = "localhost"
            rabbitmq_service_instance.exchange_name = "test_exchange"
            rabbitmq_service_instance.queue_name = "test_queue"

            rabbitmq_service_instance.connect()

            # Simulate publish error
            mock_rabbitmq['channel'].basic_publish.side_effect = Exception("Channel closed")

            with pytest.raises(Exception) as exc_info:
                rabbitmq_service_instance.publish("test.key", {"test": "data"})

            assert "Channel closed" in str(exc_info.value)

    def test_consume_starts_consumption(self, rabbitmq_service_instance, mock_rabbitmq):
        """Test that consume starts message consumption"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika', mock_rabbitmq['pika']):

            mock_settings.RABBITMQ_URL = None
            mock_settings.RABBITMQ_HOST = "localhost"
            mock_settings.RABBITMQ_PORT = 5672
            mock_settings.RABBITMQ_USER = "guest"
            mock_settings.RABBITMQ_PASSWORD = "guest"
            mock_settings.RABBITMQ_EXCHANGE_NAME = "test_exchange"
            mock_settings.RABBITMQ_QUEUE_NAME = "test_queue"

            rabbitmq_service_instance.host = "localhost"
            rabbitmq_service_instance.exchange_name = "test_exchange"
            rabbitmq_service_instance.queue_name = "test_queue"

            rabbitmq_service_instance.connect()

            # Mock callback
            callback = MagicMock()

            # Mock start_consuming to raise KeyboardInterrupt (to exit gracefully)
            mock_rabbitmq['channel'].start_consuming.side_effect = KeyboardInterrupt()

            rabbitmq_service_instance.consume(callback)

            # Verify QoS was set
            mock_rabbitmq['channel'].basic_qos.assert_called_once_with(prefetch_count=1)

            # Verify basic_consume was configured
            mock_rabbitmq['channel'].basic_consume.assert_called_once_with(
                queue="test_queue",
                on_message_callback=callback,
                auto_ack=False
            )

    def test_close_connection(self, rabbitmq_service_instance, mock_rabbitmq):
        """Test closing RabbitMQ connection"""
        with patch('app.services.rabbitmq_service.settings') as mock_settings, \
             patch('app.services.rabbitmq_service.pika', mock_rabbitmq['pika']):

            mock_settings.RABBITMQ_URL = None
            mock_settings.RABBITMQ_HOST = "localhost"
            mock_settings.RABBITMQ_PORT = 5672
            mock_settings.RABBITMQ_USER = "guest"
            mock_settings.RABBITMQ_PASSWORD = "guest"
            mock_settings.RABBITMQ_EXCHANGE_NAME = "test_exchange"
            mock_settings.RABBITMQ_QUEUE_NAME = "test_queue"

            rabbitmq_service_instance.host = "localhost"
            rabbitmq_service_instance.exchange_name = "test_exchange"
            rabbitmq_service_instance.queue_name = "test_queue"

            rabbitmq_service_instance.connect()

            mock_rabbitmq['connection'].is_closed = False

            rabbitmq_service_instance.close()

            # Verify connection was closed
            mock_rabbitmq['connection'].close.assert_called_once()

    def test_close_already_closed_connection(self, rabbitmq_service_instance):
        """Test closing an already closed connection"""
        mock_connection = MagicMock()
        mock_connection.is_closed = True

        rabbitmq_service_instance.connection = mock_connection

        rabbitmq_service_instance.close()

        # Should not attempt to close
        mock_connection.close.assert_not_called()
