# 📬 Microservicio de Notificaciones - Sistema de Gestión de Parqueaderos

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?logo=postgresql)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.12-FF6600?logo=rabbitmq)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)
![Tests](https://img.shields.io/badge/Tests-111_passing-success)
![Coverage](https://img.shields.io/badge/Coverage-60--70%25-yellow)

Microservicio desarrollado con **FastAPI** para gestionar notificaciones multicanal (email, push, WebSocket) en un sistema de gestión inteligente de parqueaderos. El servicio consume eventos de RabbitMQ publicados por otros microservicios y envía notificaciones a los usuarios según sus preferencias.

---

## 📋 Descripción General

Este microservicio actúa como el **centro de notificaciones** del ecosistema de microservicios del sistema de parqueaderos. Su responsabilidad principal es:

1. **Consumir eventos** publicados por otros microservicios (autenticación, reservas, pagos) a través de RabbitMQ
2. **Procesar notificaciones** utilizando templates personalizables con reemplazo de variables
3. **Enviar notificaciones multicanal**:
   - **WebSocket**: Notificaciones en tiempo real para usuarios conectados
   - **Push (FCM)**: Notificaciones push cuando el usuario no está conectado
   - **Email (SMTP)**: Emails transaccionales con templates HTML
4. **Gestionar preferencias** de notificación por usuario (canales habilitados, eventos suscritos)
5. **Implementar lógica de reintentos** con backoff exponencial para notificaciones fallidas
6. **Exponer API REST** para consultar notificaciones, gestionar templates y preferencias

### Características Principales

- ✅ **Arquitectura híbrida**: WebSocket → FCM → Email (fallback inteligente)
- ✅ **Sistema de templates**: Personalización de mensajes con placeholders dinámicos
- ✅ **Gestión de preferencias**: Control granular por usuario y tipo de evento
- ✅ **Reintentos automáticos**: Hasta 3 reintentos con backoff exponencial
- ✅ **CloudAMQP compatible**: Soporte para RabbitMQ local y en la nube
- ✅ **WebSocket en tiempo real**: Notificaciones instantáneas para usuarios conectados
- ✅ **Cobertura de pruebas**: pruebas unitarias y de integración (60-70% cobertura)

## 🚀 Tecnologías Utilizadas

### Backend & Framework
- **FastAPI 0.104.1**: Framework web moderno y de alto rendimiento para APIs
- **Python 3.11**: Lenguaje de programación
- **Uvicorn**: Servidor ASGI de alto rendimiento

### Base de Datos
- **PostgreSQL 15**: Base de datos relacional principal
- **SQLAlchemy 2.0**: ORM para Python
- **Alembic 1.12**: Migraciones de base de datos

### Mensajería & Comunicación
- **RabbitMQ 3.12**: Sistema de mensajería para comunicación asíncrona entre microservicios
- **Pika 1.3.2**: Cliente de RabbitMQ para Python
- **CloudAMQP**: Soporte para RabbitMQ en la nube
- **WebSockets 12.0**: Comunicación bidireccional en tiempo real

### Notificaciones
- **Firebase Cloud Messaging (FCM)**: Servicio de notificaciones push para móviles y web
- **Firebase Admin SDK 6.3.0**: SDK de Firebase para Python
- **aiosmtplib 3.0.1**: Cliente SMTP asíncrono para envío de emails
- **SMTP (Gmail)**: Protocolo de envío de emails

### Validación & Schemas
- **Pydantic 2.5.0**: Validación de datos y schemas
- **Pydantic Settings 2.1.0**: Gestión de configuración

### Testing
- **pytest 7.4.3**: Framework de testing
- **pytest-asyncio 0.21.1**: Soporte para pruebas asíncronas
- **pytest-mock 3.12.0**: Utilidades de mocking
- **Faker 20.1.0**: Generación de datos de prueba
- **httpx 0.25.2**: Cliente HTTP asíncrono para testing

### DevOps & Contenedorización
- **Docker**: Contenedorización de servicios
- **Docker Compose**: Orquestación de múltiples contenedores
- **Git**: Control de versiones

## Arquitectura

```
┌─────────────────┐      ┌──────────────────┐
│ Auth            │      │ Parking/Reserva  │
│ Microservice    │      │ Microservice     │
└────────┬────────┘      └────────┬─────────┘
         │                        │
         └────────┐      ┌────────┘
                  ▼      ▼
           ┌──────────────────┐
           │    RabbitMQ      │
           │   (Exchange)     │
           └────────┬─────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Notifications MS    │
         │  - Consumer          │
         │  - API REST          │
         └──────────┬───────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
    ┌─────────┐          ┌──────────┐
    │  Email  │          │   Push   │
    │ Service │          │ (FCM)    │
    └─────────┘          └──────────┘
```

## Estructura del Proyecto

```
ms-notifications/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py          # Endpoints REST del API
│   ├── consumers/
│   │   ├── __init__.py
│   │   └── notification_consumer.py  # Consumidor de RabbitMQ
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py             # Configuración de la aplicación
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py         # Conexión a PostgreSQL
│   ├── models/
│   │   ├── __init__.py
│   │   └── notification.py       # Modelos de base de datos
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── notification.py       # Schemas Pydantic
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email_service.py      # Servicio de envío de emails
│   │   ├── push_service.py       # Servicio de notificaciones push
│   │   ├── notification_service.py  # Lógica de negocio
│   │   └── rabbitmq_service.py   # Cliente RabbitMQ
│   ├── __init__.py
│   └── main.py                   # Aplicación FastAPI
├── migrations/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Configuración Inicial

### 1. Clonar el repositorio y crear archivo .env

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus configuraciones.

### 2. Configurar Firebase Cloud Messaging (FCM)

Para notificaciones push, necesitas configurar Firebase:

#### Pasos para obtener las credenciales de Firebase:

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Ve a **Project Settings** (⚙️ > Project Settings)
4. En la pestaña **Service accounts**
5. Click en **Generate new private key**
6. Descarga el archivo JSON
7. Guarda el archivo como `firebase-credentials.json` en la raíz del proyecto

**Estructura del archivo firebase-credentials.json:**
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

#### Obtener FCM Token en tu aplicación cliente:

**Para aplicación web (JavaScript):**
```javascript
import { getMessaging, getToken } from "firebase/messaging";

const messaging = getMessaging();
getToken(messaging, { vapidKey: 'YOUR_VAPID_KEY' })
  .then((currentToken) => {
    if (currentToken) {
      console.log('FCM Token:', currentToken);
      // Envía este token al backend para guardarlo
    }
  });
```

**Para aplicación móvil (Android - Kotlin):**
```kotlin
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        Log.d("FCM Token", token)
        // Envía este token al backend
    }
}
```

### 3. Configurar Email (Gmail)

Para envío de emails usando Gmail:

1. Activa la verificación en 2 pasos en tu cuenta de Gmail
2. Genera una contraseña de aplicación:
   - Ve a [Google Account Security](https://myaccount.google.com/security)
   - Selecciona **2-Step Verification**
   - En la parte inferior, selecciona **App passwords**
   - Genera una contraseña para "Mail"
3. Usa esta contraseña en `SMTP_PASSWORD` en tu archivo `.env`

**Configuración en .env:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-contraseña-de-aplicacion
EMAIL_FROM=noreply@parkingapp.com
EMAIL_FROM_NAME=Parking System
```

### 4. Configurar RabbitMQ

RabbitMQ se levantará automáticamente con Docker Compose. Características:

- **Exchange Type**: Topic
- **Exchange Name**: notifications_exchange
- **Queue Name**: notifications_queue
- **Routing Keys**:
  - `user.registered` - Usuario registrado
  - `user.password.reset` - Reseteo de contraseña
  - `reservation.created` - Reserva creada
  - `reservation.confirmed` - Reserva confirmada
  - `reservation.cancelled` - Reserva cancelada
  - `reservation.reminder` - Recordatorio de reserva
  - `payment.success` - Pago exitoso
  - `payment.failed` - Pago fallido
  - `parking.spot.released` - Plaza liberada

#### Acceder a RabbitMQ Management UI:
- URL: http://localhost:15672
- Usuario: guest
- Contraseña: guest

## 🔧 Instalación y Ejecución

### Opción 1: Con Docker Compose (⭐ Recomendado)

Esta es la forma más sencilla de levantar el microservicio completo con todos sus servicios.

#### Paso 1: Preparar el archivo .env

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar las variables de entorno necesarias
# IMPORTANTE: Configura al menos:
# - DATABASE_URL (se usa automáticamente con docker-compose)
# - RABBITMQ_URL (CloudAMQP) o configuración local
# - SMTP_* (credenciales de email)
# - FIREBASE_CREDENTIALS_PATH (opcional, para push notifications)
```

**Configuración mínima para empezar (.env):**

```env
# Base de datos (automática con docker-compose)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/notifications_db

# RabbitMQ - CloudAMQP (recomendado)
RABBITMQ_URL=amqps://tu-usuario:tu-password@host.rmq.cloudamqp.com/vhost

# O usar RabbitMQ local (descomenta la sección en docker-compose.yml)
# RABBITMQ_HOST=rabbitmq
# RABBITMQ_PORT=5672
# RABBITMQ_USER=guest
# RABBITMQ_PASSWORD=guest

# Configuración de Queue
RABBITMQ_QUEUE_NAME=notifications_queue
RABBITMQ_EXCHANGE_NAME=notifications

# Email (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password  # Contraseña de aplicación de Gmail
EMAIL_FROM=noreply@parkingapp.com
EMAIL_FROM_NAME=Parking System

# Firebase (opcional - para push notifications)
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# API
API_HOST=0.0.0.0
API_PORT=8003
DEBUG=True

# Retry
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=60
```

#### Paso 2: Levantar los servicios

```bash
# Construir y levantar todos los servicios en segundo plano
docker-compose up -d

# Ver el estado de los servicios
docker-compose ps
```

**Servicios levantados:**
- ✅ **postgres**: Base de datos PostgreSQL (puerto 5432)
- ✅ **notifications-api**: API REST de FastAPI (puerto 8003)
- ✅ **notifications-consumer**: Consumer de RabbitMQ (escucha eventos)

#### Paso 3: Verificar que todo funciona

```bash
# Ver logs en tiempo real de todos los servicios
docker-compose logs -f

# Ver logs solo del consumer (importante para ver eventos procesados)
docker-compose logs -f notifications-consumer

# Ver logs solo de la API
docker-compose logs -f notifications-api

# Probar el health check
curl http://localhost:8003/health
# Respuesta esperada: {"status":"healthy","service":"notifications"}

# Ver la documentación interactiva (Swagger)
# Abre en tu navegador: http://localhost:8003/docs
```

#### Paso 4: El consumer está escuchando eventos de RabbitMQ

El servicio `notifications-consumer` ya está **escuchando activamente** los eventos de RabbitMQ. Verás en los logs algo como:

```
notifications-consumer | INFO - Connected to RabbitMQ at host.rmq.cloudamqp.com:5672
notifications-consumer | INFO - Queue 'notifications_queue' bound to exchange 'notifications'
notifications-consumer | INFO - Waiting for messages in queue 'notifications_queue'...
```

**Routing keys que el consumer está escuchando:**

- `email.verification` → Verificación de email
- `email.welcome` → Bienvenida al usuario
- `email.password_reset` → Reset de contraseña
- `email.password_changed` → Contraseña cambiada
- `reservation.created` → Reserva creada
- `reservation.confirmed` → Reserva confirmada
- `reservation.cancelled` → Reserva cancelada
- `reservation.reminder` → Recordatorio de reserva
- `payment.success` → Pago exitoso
- `payment.failed` → Pago fallido
- `parking.spot.released` → Plaza liberada

#### Comandos útiles de Docker Compose

```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (¡cuidado! borra la BD)
docker-compose down -v

# Reconstruir las imágenes después de cambios en el código
docker-compose up -d --build

# Reiniciar un servicio específico
docker-compose restart notifications-consumer

# Ver logs de los últimos 100 líneas
docker-compose logs --tail=100

# Ejecutar comando en un contenedor
docker-compose exec notifications-api python -c "print('Hello')"
```

---

### Opción 2: Desarrollo Local (Sin Docker para la API)

Útil si quieres debuggear o desarrollar sin contenedores.

#### Paso 1: Preparar el entorno

```bash
# Crear entorno virtual de Python
python -m venv venv

# Activar el entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### Paso 2: Levantar solo la infraestructura con Docker

```bash
# Levantar solo PostgreSQL (RabbitMQ en la nube con CloudAMQP)
docker-compose up -d postgres

# Si quieres usar RabbitMQ local, descomenta la sección en docker-compose.yml
# y ejecuta:
# docker-compose up -d postgres rabbitmq
```

**NOTA**: Si usas RabbitMQ local, ajusta el `.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/notifications_db
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
```

#### Paso 3: Ejecutar la API localmente

```bash
# Ejecutar la API de FastAPI con hot-reload
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

La API estará disponible en:
- http://localhost:8003
- Docs: http://localhost:8003/docs

#### Paso 4: Ejecutar el consumer en otra terminal

```bash
# Activar el entorno virtual en otra terminal
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Ejecutar el consumer de RabbitMQ
python -m app.consumers.notification_consumer
```

**Salida esperada del consumer:**

```
INFO - Connected to RabbitMQ at localhost:5672
INFO - Queue 'notifications_queue' bound to exchange 'notifications'
INFO - Waiting for messages in queue 'notifications_queue'...
```

El consumer ahora está **escuchando eventos** de RabbitMQ y procesará automáticamente cualquier mensaje que llegue.

---

### 🎯 Servicios Disponibles

Una vez levantados los servicios, estarán disponibles en:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **API REST** | http://localhost:8003 | Endpoints REST del microservicio |
| **Swagger Docs** | http://localhost:8003/docs | Documentación interactiva de la API |
| **ReDoc** | http://localhost:8003/redoc | Documentación alternativa |
| **Health Check** | http://localhost:8003/health | Verificación de estado del servicio |
| **PostgreSQL** | localhost:5432 | Base de datos (postgres/postgres) |
| **WebSocket** | ws://localhost:8003/ws/notifications | Endpoint de WebSocket para notificaciones en tiempo real |

**RabbitMQ Management (solo si usas local):**
- URL: http://localhost:15672
- Usuario: guest
- Contraseña: guest

## Uso del API

### 1. Crear Templates de Notificación

Antes de enviar notificaciones, debes crear templates:

```bash
curl -X POST "http://localhost:8003/api/v1/templates" \
-H "Content-Type: application/json" \
-d '{
  "event_type": "RESERVATION_CONFIRMED",
  "notification_type": "email",
  "subject_template": "Reserva Confirmada - {parking_name}",
  "body_template": "Tu reserva en {parking_name} ha sido confirmada. Fecha: {start_time}. Total: ${price}",
  "priority": "normal",
  "is_active": true
}'
```

```bash
curl -X POST "http://localhost:8003/api/v1/templates" \
-H "Content-Type: application/json" \
-d '{
  "event_type": "RESERVATION_CONFIRMED",
  "notification_type": "push",
  "title_template": "Reserva Confirmada",
  "body_template": "Tu reserva en {parking_name} está confirmada para {start_time}",
  "priority": "high",
  "is_active": true
}'
```

### 2. Registrar Preferencias de Usuario

```bash
curl -X POST "http://localhost:8003/api/v1/preferences" \
-H "Content-Type: application/json" \
-d '{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "fcm_token": "tu-fcm-token-aqui",
  "email_enabled": true,
  "push_enabled": true,
  "event_preferences": {
    "RESERVATION_CONFIRMED": {
      "email": true,
      "push": true
    }
  }
}'
```

### 3. Enviar Notificación desde otro Microservicio

Los otros microservicios deben publicar mensajes a RabbitMQ:

**Ejemplo en Python:**

```python
import pika
import json

# Conectar a RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

# Mensaje de notificación
message = {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_email": "usuario@example.com",
    "fcm_token": "token-fcm-del-usuario",
    "event_type": "RESERVATION_CONFIRMED",
    "data": {
        "reservation_id": "987e6543-e21b-12d3-a456-426614174999",
        "parking_name": "Parking Centro",
        "start_time": "2025-11-10T08:00:00Z",
        "end_time": "2025-11-10T18:00:00Z",
        "price": 15.00
    },
    "priority": "normal"
}

# Publicar en RabbitMQ
channel.basic_publish(
    exchange='notifications_exchange',
    routing_key='reservation.confirmed',
    body=json.dumps(message),
    properties=pika.BasicProperties(
        delivery_mode=2,  # Mensaje persistente
        content_type='application/json'
    )
)

print("Notificación enviada!")
connection.close()
```

**Ejemplo en Node.js:**

```javascript
const amqp = require('amqplib');

async function sendNotification() {
  const connection = await amqp.connect('amqp://localhost');
  const channel = await connection.createChannel();

  const exchange = 'notifications_exchange';
  const routingKey = 'reservation.confirmed';

  const message = {
    user_id: "123e4567-e89b-12d3-a456-426614174000",
    user_email: "usuario@example.com",
    fcm_token: "token-fcm-del-usuario",
    event_type: "RESERVATION_CONFIRMED",
    data: {
      reservation_id: "987e6543-e21b-12d3-a456-426614174999",
      parking_name: "Parking Centro",
      start_time: "2025-11-10T08:00:00Z",
      end_time: "2025-11-10T18:00:00Z",
      price: 15.00
    },
    priority: "normal"
  };

  channel.publish(
    exchange,
    routingKey,
    Buffer.from(JSON.stringify(message)),
    { persistent: true, contentType: 'application/json' }
  );

  console.log('Notificación enviada!');

  await channel.close();
  await connection.close();
}

sendNotification();
```

## Endpoints del API

### Notificaciones

- `GET /api/v1/notifications` - Listar todas las notificaciones
- `GET /api/v1/notifications/{notification_id}` - Obtener notificación por ID
- `GET /api/v1/notifications/user/{user_id}` - Notificaciones de un usuario

### Templates

- `GET /api/v1/templates` - Listar templates
- `GET /api/v1/templates/{event_type}` - Templates por evento
- `POST /api/v1/templates` - Crear template
- `PUT /api/v1/templates/{template_id}` - Actualizar template
- `DELETE /api/v1/templates/{template_id}` - Eliminar template

### Preferencias de Usuario

- `GET /api/v1/preferences/{user_id}` - Obtener preferencias
- `POST /api/v1/preferences` - Crear preferencias
- `PUT /api/v1/preferences/{user_id}` - Actualizar preferencias
- `PUT /api/v1/preferences/{user_id}/fcm-token` - Actualizar FCM token

### Health Check

- `GET /api/v1/health` - Estado del servicio
- `GET /` - Información del servicio

## Tipos de Eventos Soportados

| Evento | Routing Key | Descripción |
|--------|-------------|-------------|
| Usuario registrado | `user.registered` | Bienvenida al nuevo usuario |
| Reseteo de contraseña | `user.password.reset` | Instrucciones para resetear contraseña |
| Reserva creada | `reservation.created` | Confirmación de creación de reserva |
| Reserva confirmada | `reservation.confirmed` | Confirmación de pago y reserva |
| Reserva cancelada | `reservation.cancelled` | Notificación de cancelación |
| Recordatorio de reserva | `reservation.reminder` | Recordatorio antes de la reserva |
| Pago exitoso | `payment.success` | Confirmación de pago |
| Pago fallido | `payment.failed` | Notificación de fallo en pago |
| Plaza liberada | `parking.spot.released` | Notificación de disponibilidad |

## Base de Datos

### Tablas Principales

1. **notifications**: Registro de todas las notificaciones enviadas
2. **notification_templates**: Templates para cada tipo de evento
3. **user_notification_preferences**: Preferencias de notificación por usuario

### Migraciones

Para crear las tablas manualmente:

```bash
# Las tablas se crean automáticamente al iniciar la aplicación
# Si necesitas recrearlas:
docker-compose exec notifications-api python -c "from app.database.connection import Base, engine; Base.metadata.create_all(bind=engine)"
```

## Monitoreo y Logs

```bash
# Ver logs del API
docker-compose logs -f notifications-api

# Ver logs del consumer
docker-compose logs -f notifications-consumer

# Ver logs de RabbitMQ
docker-compose logs -f rabbitmq

# Ver logs de PostgreSQL
docker-compose logs -f postgres
```

## Testing

Para probar el envío de notificaciones:

```bash
# Publicar mensaje de prueba a RabbitMQ
docker-compose exec rabbitmq rabbitmqadmin publish \
  exchange=notifications_exchange \
  routing_key=reservation.confirmed \
  payload='{"user_id":"123e4567-e89b-12d3-a456-426614174000","user_email":"test@example.com","event_type":"RESERVATION_CONFIRMED","data":{"parking_name":"Test Parking","price":15.00}}'
```

## Troubleshooting

### Error: Firebase credentials not found

**Solución**: Asegúrate de tener el archivo `firebase-credentials.json` en la raíz del proyecto.

### Error: Cannot connect to RabbitMQ

**Solución**: Verifica que RabbitMQ esté corriendo:
```bash
docker-compose ps
docker-compose up -d rabbitmq
```

### Error: Email not sending

**Solución**:
1. Verifica que tengas una contraseña de aplicación válida de Gmail
2. Revisa que el SMTP_HOST y SMTP_PORT sean correctos
3. Verifica los logs para más detalles

### Error: Push notifications not working

**Solución**:
1. Verifica que el archivo de credenciales de Firebase sea válido
2. Asegúrate de que el FCM token del usuario sea correcto y esté actualizado
3. Verifica que el proyecto de Firebase tenga Cloud Messaging habilitado

## Seguridad

Para producción, asegúrate de:

1. Cambiar las credenciales por defecto de RabbitMQ
2. Usar HTTPS para el API
3. Implementar autenticación JWT para los endpoints
4. Configurar CORS correctamente
5. No exponer puertos innecesarios
6. Usar secretos seguros para las variables de entorno
7. Implementar rate limiting

## ✅ Testing

El proyecto cuenta con una suite completa de pruebas unitarias y de integración. Ver [TESTING.md](TESTING.md) para documentación detallada.

### Ejecutar Pruebas

```bash
# Todas las pruebas
pytest

# Solo pruebas unitarias
pytest -m unit

# Solo pruebas de integración
pytest -m integration

# Con verbose
pytest -v

# Con cobertura
pytest --cov=app --cov-report=html
```

### Estadísticas de Testing

- **Pruebas Unitarias**: ~75 pruebas
- **Pruebas de Modelos**: 15 pruebas
- **Pruebas de Integración**: ~21 pruebas
- **Total**: ~111 pruebas
- **Cobertura**: 60-70%

### Áreas Cubiertas

- ✅ Servicios principales (notification, email, push, rabbitmq)
- ✅ Modelos de base de datos
- ✅ API endpoints (CRUD completo)
- ✅ Manejo de errores y reintentos
- ✅ WebSocket fallback
- ✅ Template rendering
- ✅ Preferencias de usuario

## 🚀 Próximas Mejoras

- [ ] Implementar autenticación JWT para endpoints
- [ ] Añadir soporte para SMS (Twilio/AWS SNS)
- [ ] Añadir métricas y monitoring (Prometheus/Grafana)
- [ ] Implementar circuit breaker pattern
- [ ] Implementar caché con Redis para templates
- [ ] Añadir soporte para notificaciones en batch
- [ ] Implementar rate limiting por usuario
- [ ] Añadir soporte para webhooks de entrega
- [ ] Implementar sistema de A/B testing para templates
- [ ] Añadir analytics de apertura/click para emails

## Licencia

MIT

## Contacto

Para preguntas o soporte, contacta al equipo de desarrollo.
