from fastapi import WebSocket
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Gestiona las conexiones WebSocket activas por usuario.

    Permite enviar notificaciones en tiempo real a usuarios conectados.
    Si un usuario no está conectado, la notificación se envía vía FCM.
    """

    def __init__(self):
        # Diccionario: user_id -> Set[WebSocket]
        # Un usuario puede tener múltiples conexiones (ej: móvil + web)
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Acepta una nueva conexión WebSocket para un usuario.

        Args:
            websocket: La conexión WebSocket
            user_id: ID del usuario (UUID como string)
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)

        logger.info(
            f"Usuario {user_id} conectado via WebSocket. "
            f"Total conexiones activas: {len(self.active_connections[user_id])}"
        )

    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Desconecta un WebSocket de un usuario.

        Args:
            websocket: La conexión WebSocket a cerrar
            user_id: ID del usuario
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # Si el usuario no tiene más conexiones activas, eliminar del dict
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

            logger.info(
                f"Usuario {user_id} desconectado. "
                f"Conexiones restantes: {len(self.active_connections.get(user_id, []))}"
            )

    def is_user_connected(self, user_id: str) -> bool:
        """
        Verifica si un usuario tiene al menos una conexión WebSocket activa.

        Args:
            user_id: ID del usuario

        Returns:
            True si el usuario está conectado, False en caso contrario
        """
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    async def send_notification(self, user_id: str, notification: dict) -> bool:
        """
        Envía una notificación a todas las conexiones activas de un usuario.

        Args:
            user_id: ID del usuario
            notification: Diccionario con los datos de la notificación

        Returns:
            True si se envió a al menos una conexión, False si no hay conexiones activas
        """
        if user_id not in self.active_connections:
            logger.debug(f"Usuario {user_id} no tiene conexiones WebSocket activas")
            return False

        disconnected = set()
        sent_count = 0

        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(notification)
                sent_count += 1
                logger.debug(f"Notificación enviada via WebSocket a usuario {user_id}")
            except Exception as e:
                logger.error(f"Error enviando notificación via WebSocket: {e}")
                disconnected.add(websocket)

        # Limpiar conexiones que fallaron
        for ws in disconnected:
            self.active_connections[user_id].discard(ws)

        # Si se eliminaron todas las conexiones, limpiar el usuario
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]

        return sent_count > 0

    async def broadcast(self, message: dict):
        """
        Envía un mensaje a TODOS los usuarios conectados.

        Args:
            message: Diccionario con el mensaje a enviar
        """
        disconnected_users = []

        for user_id, connections in self.active_connections.items():
            disconnected = set()

            for websocket in connections:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting a usuario {user_id}: {e}")
                    disconnected.add(websocket)

            # Limpiar conexiones fallidas
            for ws in disconnected:
                connections.discard(ws)

            # Marcar usuario para eliminación si no tiene conexiones
            if not connections:
                disconnected_users.append(user_id)

        # Limpiar usuarios sin conexiones
        for user_id in disconnected_users:
            del self.active_connections[user_id]

        logger.info(f"Broadcast enviado a {len(self.active_connections)} usuarios")

    def get_connected_users_count(self) -> int:
        """Retorna el número de usuarios únicos conectados."""
        return len(self.active_connections)

    def get_total_connections_count(self) -> int:
        """Retorna el número total de conexiones WebSocket activas."""
        return sum(len(connections) for connections in self.active_connections.values())


# Singleton global
manager = ConnectionManager()
