"""
Script to seed authentication email templates into the database
Run this script once to create the required templates for authentication events
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database.connection import SessionLocal
from app.models.notification import NotificationTemplate, NotificationType, NotificationPriority
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_auth_templates():
    """Create email templates for authentication events"""
    db = SessionLocal()

    try:
        templates = [
            # Email Verification Template
            {
                "event_type": "EMAIL_VERIFICATION",
                "notification_type": NotificationType.EMAIL,
                "subject_template": "Verifica tu cuenta de Easy Parking",
                "body_template": """
                    <p>Hola {name},</p>

                    <p>¡Gracias por registrarte en Easy Parking! Para completar tu registro y comenzar a usar nuestra plataforma,
                    necesitamos verificar tu dirección de email.</p>

                    <p>Por favor, haz clic en el siguiente botón para verificar tu cuenta:</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_link}"
                           style="background-color: #4CAF50; color: white; padding: 12px 30px;
                                  text-decoration: none; border-radius: 5px; display: inline-block;
                                  font-weight: bold;">
                            Verificar mi cuenta
                        </a>
                    </div>

                    <p>O copia y pega este enlace en tu navegador:</p>
                    <p style="word-break: break-all; color: #666;">{verification_link}</p>

                    <p><strong>⏰ Este enlace expirará en 24 horas.</strong></p>

                    <p>Si no creaste esta cuenta, puedes ignorar este email.</p>

                    <p>Saludos,<br>El equipo de Easy Parking</p>
                """,
                "priority": NotificationPriority.HIGH,
                "is_active": 1
            },
            # Welcome Email Template
            {
                "event_type": "EMAIL_WELCOME",
                "notification_type": NotificationType.EMAIL,
                "subject_template": "¡Bienvenido a Easy Parking!",
                "body_template": """
                    <p>Hola {name},</p>

                    <p>¡Tu cuenta ha sido verificada exitosamente! 🎉</p>

                    <p>Bienvenido a Easy Parking, la forma más fácil y conveniente de encontrar y reservar estacionamiento.</p>

                    <h3>¿Qué puedes hacer ahora?</h3>
                    <ul>
                        <li>🚗 Buscar y reservar espacios de estacionamiento cerca de ti</li>
                        <li>💳 Pagar de forma segura desde la aplicación</li>
                        <li>📱 Recibir notificaciones sobre tus reservas</li>
                        <li>⭐ Guardar tus estacionamientos favoritos</li>
                    </ul>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{frontend_url}/login"
                           style="background-color: #4CAF50; color: white; padding: 12px 30px;
                                  text-decoration: none; border-radius: 5px; display: inline-block;
                                  font-weight: bold;">
                            Comenzar ahora
                        </a>
                    </div>

                    <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>

                    <p>¡Feliz estacionamiento!<br>El equipo de Easy Parking</p>
                """,
                "priority": NotificationPriority.NORMAL,
                "is_active": 1
            },
            # Password Reset Template
            {
                "event_type": "EMAIL_PASSWORD_RESET",
                "notification_type": NotificationType.EMAIL,
                "subject_template": "Restablece tu contraseña de Easy Parking",
                "body_template": """
                    <p>Hola {name},</p>

                    <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta de Easy Parking.</p>

                    <p>Si fuiste tú quien solicitó esto, haz clic en el botón de abajo para crear una nueva contraseña:</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}"
                           style="background-color: #4CAF50; color: white; padding: 12px 30px;
                                  text-decoration: none; border-radius: 5px; display: inline-block;
                                  font-weight: bold;">
                            Restablecer contraseña
                        </a>
                    </div>

                    <p>O copia y pega este enlace en tu navegador:</p>
                    <p style="word-break: break-all; color: #666;">{reset_link}</p>

                    <p><strong>⏰ Este enlace expirará en 1 hora.</strong></p>

                    <p><strong>⚠️ Importante:</strong> Si no solicitaste restablecer tu contraseña,
                    ignora este email. Tu contraseña permanecerá sin cambios y tu cuenta estará segura.</p>

                    <p>Saludos,<br>El equipo de Easy Parking</p>
                """,
                "priority": NotificationPriority.HIGH,
                "is_active": 1
            },
            # Password Changed Confirmation Template
            {
                "event_type": "EMAIL_PASSWORD_CHANGED",
                "notification_type": NotificationType.EMAIL,
                "subject_template": "Tu contraseña ha sido cambiada",
                "body_template": """
                    <p>Hola {name},</p>

                    <p>Te confirmamos que la contraseña de tu cuenta de Easy Parking ha sido cambiada exitosamente.</p>

                    <div style="background-color: #e8f5e9; border-left: 4px solid #4CAF50; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0;">✅ Tu cuenta ahora está protegida con tu nueva contraseña.</p>
                    </div>

                    <p>A partir de ahora, deberás usar tu nueva contraseña para iniciar sesión.</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{frontend_url}/login"
                           style="background-color: #4CAF50; color: white; padding: 12px 30px;
                                  text-decoration: none; border-radius: 5px; display: inline-block;
                                  font-weight: bold;">
                            Iniciar sesión
                        </a>
                    </div>

                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>⚠️ ¿No fuiste tú?</strong></p>
                        <p style="margin: 10px 0 0 0;">Si no realizaste este cambio, tu cuenta puede estar comprometida.
                        Por favor, contacta a nuestro equipo de soporte inmediatamente.</p>
                    </div>

                    <p>Saludos,<br>El equipo de Easy Parking</p>
                """,
                "priority": NotificationPriority.HIGH,
                "is_active": 1
            }
        ]

        # Insert templates
        created_count = 0
        for template_data in templates:
            # Check if template already exists
            existing = db.query(NotificationTemplate).filter_by(
                event_type=template_data["event_type"],
                notification_type=template_data["notification_type"]
            ).first()

            if existing:
                logger.info(f"Template {template_data['event_type']} already exists, skipping...")
                continue

            # Create new template
            template = NotificationTemplate(**template_data)
            db.add(template)
            created_count += 1
            logger.info(f"Created template: {template_data['event_type']}")

        db.commit()
        logger.info(f"✅ Successfully created {created_count} authentication email templates")

        if created_count < len(templates):
            logger.info(f"ℹ️  {len(templates) - created_count} templates already existed")

    except Exception as e:
        logger.error(f"❌ Error creating templates: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting authentication templates seeding...")
    create_auth_templates()
    logger.info("Done!")
