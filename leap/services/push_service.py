import asyncio
import fastapi
import logging

from leap.models import message
from leap.utils import singleton


@singleton.singleton
class PushService(object):

    def __init__(self) -> None:
        # 存储所有连接的 WebSocket 客户端
        self._active_connections: list[fastapi.WebSocket] = []

        self._logger = logging.getLogger(__name__)

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._logger.info("Event loop set for PushService")

    def add_connection(self, websocket: fastapi.WebSocket) -> None:
        self._active_connections.append(websocket)
        self._logger.info(
            f"New WebSocket connection added: {websocket.client}. Total connections: {len(self._active_connections)}")

    def push_message(self, xt_message: message.XtMessage):
        """Push the message to message queue. This is the only one called in the callback thread."""
        self._logger.info(f"Message to be pushed: {xt_message}")

        asyncio.run_coroutine_threadsafe(
            self.notify_subscribers(xt_message),
            self._loop
        )

    async def notify_subscribers(self, xt_message: message.XtMessage):
        if not self._active_connections:
            self._logger.info(
                "No active WebSocket connections to push message to.")
            return

        remove_list: list[fastapi.WebSocket] = []
        for connection in self._active_connections:
            try:
                await connection.send_text(xt_message.model_dump_json())
                self._logger.info(
                    f"Message sent to {connection.client}: {xt_message.type}")
            except Exception as e:
                self._logger.error(
                    f"Error sending message to client: {e}. Closing connection. Application state: {connection.application_state}. Client state: {connection.client_state}.")
                remove_list.append(connection)
        for conn in remove_list:
            self._active_connections.remove(conn)
