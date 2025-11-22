"""
Unit tests for email_service.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.email_service import email_service


@pytest.mark.unit
class TestEmailService:
    """Test suite for EmailService"""

    @pytest.mark.asyncio
    async def test_send_email_success_html(self, mock_smtp):
        """Test successful HTML email sending"""
        with patch('app.services.email_service.aiosmtplib.send', new=AsyncMock()) as mock_send:
            result = await email_service.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                body="<h1>Test HTML Body</h1>",
                is_html=True
            )

            assert result is True
            mock_send.assert_called_once()

            # Verify message structure
            call_args = mock_send.call_args
            message = call_args[0][0]
            assert message["To"] == "test@example.com"
            assert message["Subject"] == "Test Subject"
            assert email_service.email_from in message["From"]

    @pytest.mark.asyncio
    async def test_send_email_success_plain_text(self):
        """Test successful plain text email sending"""
        with patch('app.services.email_service.aiosmtplib.send', new=AsyncMock()) as mock_send:
            result = await email_service.send_email(
                to_email="test@example.com",
                subject="Plain Text Test",
                body="This is plain text content",
                is_html=False
            )

            assert result is True
            mock_send.assert_called_once()

            # Verify message uses plain text
            call_args = mock_send.call_args
            message = call_args[0][0]
            payload = message.get_payload()[0]
            assert payload.get_content_type() == "text/plain"

    @pytest.mark.asyncio
    async def test_send_email_failure_smtp_error(self):
        """Test email sending failure due to SMTP error"""
        with patch('app.services.email_service.aiosmtplib.send',
                   new=AsyncMock(side_effect=Exception("SMTP connection failed"))):
            result = await email_service.send_email(
                to_email="test@example.com",
                subject="Test",
                body="Body"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_email_failure_invalid_credentials(self):
        """Test email sending failure due to authentication error"""
        with patch('app.services.email_service.aiosmtplib.send',
                   new=AsyncMock(side_effect=Exception("Authentication failed"))):
            result = await email_service.send_email(
                to_email="test@example.com",
                subject="Test",
                body="Body"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_email_with_special_characters(self):
        """Test email sending with special characters in subject and body"""
        with patch('app.services.email_service.aiosmtplib.send', new=AsyncMock()) as mock_send:
            result = await email_service.send_email(
                to_email="test@example.com",
                subject="Confirmación de Reservación ñáéíóú",
                body="<p>Hola! Tu reservación está confirmada 🎉</p>",
                is_html=True
            )

            assert result is True
            mock_send.assert_called_once()

    def test_generate_html_template_basic(self):
        """Test HTML template generation without additional data"""
        html = email_service.generate_html_template(
            title="Welcome Email",
            body="Thank you for registering!"
        )

        assert "<!DOCTYPE html>" in html
        assert "Welcome Email" in html
        assert "Thank you for registering!" in html
        assert "Parking System" in html

    def test_generate_html_template_with_data(self):
        """Test HTML template generation with additional data"""
        data = {
            "parking_name": "Downtown Parking",
            "reservation_id": "RES-12345",
            "price": "$15.00"
        }

        html = email_service.generate_html_template(
            title="Reservation Confirmed",
            body="Your reservation has been confirmed",
            data=data
        )

        assert "Reservation Confirmed" in html
        assert "Your reservation has been confirmed" in html
        assert "Downtown Parking" in html
        assert "RES-12345" in html
        assert "$15.00" in html
        assert "data-item" in html

    def test_generate_html_template_styling(self):
        """Test that HTML template includes proper styling"""
        html = email_service.generate_html_template(
            title="Test",
            body="Content"
        )

        # Verify CSS styles are present
        assert "<style>" in html
        assert "font-family" in html
        assert ".header" in html
        assert ".content" in html
        assert ".footer" in html
        assert "background-color" in html

    def test_generate_html_template_responsive(self):
        """Test that HTML template includes responsive meta tags"""
        html = email_service.generate_html_template(
            title="Test",
            body="Content"
        )

        assert 'meta name="viewport"' in html
        assert 'charset="UTF-8"' in html

    def test_generate_html_template_empty_data(self):
        """Test HTML template generation with empty data dict"""
        html = email_service.generate_html_template(
            title="Test Title",
            body="Test Body",
            data={}
        )

        assert "Test Title" in html
        assert "Test Body" in html
        # Should not have data-item divs
        assert "data-section" not in html

    def test_generate_html_template_footer_content(self):
        """Test that footer contains expected content"""
        html = email_service.generate_html_template(
            title="Test",
            body="Content"
        )

        assert "2025 Parking System" in html
        assert "Todos los derechos reservados" in html
        assert "correo automático" in html

    @pytest.mark.asyncio
    async def test_send_email_smtp_configuration(self):
        """Test that SMTP configuration is used correctly"""
        with patch('app.services.email_service.aiosmtplib.send', new=AsyncMock()) as mock_send:
            await email_service.send_email(
                to_email="test@example.com",
                subject="Test",
                body="Body"
            )

            # Verify SMTP configuration parameters
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs['hostname'] == email_service.smtp_host
            assert call_kwargs['port'] == email_service.smtp_port
            assert call_kwargs['username'] == email_service.smtp_user
            assert call_kwargs['password'] == email_service.smtp_password
            assert call_kwargs['start_tls'] is True

    @pytest.mark.asyncio
    async def test_send_email_message_encoding(self):
        """Test that email messages are properly UTF-8 encoded"""
        with patch('app.services.email_service.aiosmtplib.send', new=AsyncMock()) as mock_send:
            await email_service.send_email(
                to_email="test@example.com",
                subject="Test with émojis 🚗",
                body="Contént with spéciål characters ñ"
            )

            call_args = mock_send.call_args
            message = call_args[0][0]
            payload = message.get_payload()[0]

            # Verify UTF-8 encoding
            assert payload.get_charset() == "utf-8"
