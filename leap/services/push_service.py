import asyncio
import fastapi
import logging
import threading

from leap.models import message
from leap.utils import singleton


@singleton.singleton
class PushService(object):

    def __init__(self) -> None:
        # 存储所有连接的 WebSocket 客户端
        self._active_connections: list[fastapi.WebSocket] = []
        self._lock = threading.Lock()

        self._logger = logging.getLogger()

    def add_connection(self, websocket: fastapi.WebSocket) -> None:
        with self._lock:
            self._active_connections.append(websocket)

    def notify_subscribers(self, xt_message: message.XtMessage):
        """通知所有连接的客户端"""
        asyncio.run(self._notify_subscribers_async(
            xt_message.model_dump_json()))

    async def _notify_subscribers_async(self, xt_message: str):
        with self._lock:
            if not self._active_connections:
                return

            remove_list: list[fastapi.WebSocket] = []
            for connection in self._active_connections:
                try:
                    await connection.send_text(xt_message)
                except Exception as e:
                    self._logger.error(
                        f"Error sending message to client: {e}. Closing connection. Application state: {connection.application_state}. Client state: {connection.client_state}.")
                    remove_list.append(connection)
            for conn in remove_list:
                self._active_connections.remove(conn)
