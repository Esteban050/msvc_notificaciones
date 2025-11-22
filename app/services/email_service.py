import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM
        self.email_from_name = settings.EMAIL_FROM_NAME

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = True
    ) -> bool:
        """
        Send an email using SMTP

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (can be plain text or HTML)
            is_html: Whether the body is HTML (default: True)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.email_from_name} <{self.email_from}>"
            message["To"] = to_email
            message["Subject"] = subject

            # Add body
            mime_type = "html" if is_html else "plain"
            message.attach(MIMEText(body, mime_type, "utf-8"))

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def generate_html_template(self, title: str, body: str, data: dict = None) -> str:
        """
        Generate a basic HTML email template

        Args:
            title: Email title
            body: Main content
            data: Additional data to include in the email

        Returns:
            str: HTML email content
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border: 1px solid #ddd;
                }}
                .footer {{
                    background-color: #333;
                    color: white;
                    padding: 10px;
                    text-align: center;
                    font-size: 12px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    margin: 10px 0;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                }}
                .data-item {{
                    margin: 10px 0;
                    padding: 10px;
                    background-color: white;
                    border-left: 3px solid #4CAF50;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
            </div>
            <div class="content">
                <p>{body}</p>
                """

        if data:
            html += "<div class='data-section'>"
            for key, value in data.items():
                html += f"<div class='data-item'><strong>{key}:</strong> {value}</div>"
            html += "</div>"

        html += """
            </div>
            <div class="footer">
                <p>&copy; 2025 Parking System. Todos los derechos reservados.</p>
                <p>Este es un correo automático, por favor no responder.</p>
            </div>
        </body>
        </html>
        """
        return html


# Singleton instance
email_service = EmailService()
