from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from app.websockets.connection_manager import manager
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/notifications")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID (UUID)")
):
    """
    WebSocket endpoint para recibir notificaciones en tiempo real.

    El cliente debe conectarse pasando su user_id como query parameter:
    ws://localhost:8003/ws/notifications?user_id=123e4567-e89b-12d3-a456-426614174000

    Una vez conectado, el cliente recibirá notificaciones en formato JSON:
    {
        "id": "notification-uuid",
        "type": "push" | "email",
        "event_type": "RESERVATION_CONFIRMED",
        "title": "Reserva Confirmada",
        "body": "Tu reserva ha sido confirmada...",
        "data": {...},
        "created_at": "2025-11-15T10:30:00Z",
        "priority": "high"
    }

    El cliente puede enviar "ping" para mantener la conexión viva,
    y recibirá "pong" como respuesta.
    """
    await manager.connect(websocket, user_id)

    try:
        # Enviar mensaje de bienvenida
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "user_id": user_id,
            "message": "Conectado a notificaciones en tiempo real"
        })

        # Mantener conexión viva y escuchar mensajes del cliente
        while True:
            # Esperar mensaje del cliente
            data = await websocket.receive_text()

            # Heartbeat: ping-pong
            if data == "ping":
                await websocket.send_text("pong")
                logger.debug(f"Heartbeat recibido de usuario {user_id}")

            # Mensaje JSON del cliente
            elif data.startswith("{"):
                try:
                    message = json.loads(data)

                    # El cliente puede solicitar información
                    if message.get("action") == "get_status":
                        await websocket.send_json({
                            "type": "status",
                            "connected": True,
                            "user_id": user_id,
                            "total_connections": manager.get_total_connections_count()
                        })

                except json.JSONDecodeError:
                    logger.warning(f"Mensaje JSON inválido de usuario {user_id}: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"Usuario {user_id} desconectado normalmente")

    except Exception as e:
        logger.error(f"Error en WebSocket para usuario {user_id}: {e}")
        manager.disconnect(websocket, user_id)


@router.get("/ws/stats")
async def websocket_stats():
    """
    Endpoint para obtener estadísticas de conexiones WebSocket activas.

    Útil para monitoreo y debugging.
    """
    return {
        "connected_users": manager.get_connected_users_count(),
        "total_connections": manager.get_total_connections_count()
    }
