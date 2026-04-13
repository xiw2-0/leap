import asyncio
import datetime as dt
import fastapi
import logging
import time
import typing

from leap.models import message, trade
from leap.services import stats_service
from leap.utils import singleton


@singleton.singleton
class PushService(object):

    def __init__(self) -> None:
        # 存储所有连接的 WebSocket 客户端
        self._active_connections: list[fastapi.WebSocket] = []

        self._logger = logging.getLogger(__name__)
        self._stats_service = stats_service.StatsService()

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._logger.info("Event loop set for PushService")

    def add_connection(self, websocket: fastapi.WebSocket) -> None:
        self._active_connections.append(websocket)
        self._logger.info(
            f"New WebSocket connection added: {websocket.client}. Total connections: {len(self._active_connections)}")

    def push_trade_message(self, xt_message: message.XtMessage):
        """Push the message to message queue. This is the one that will be called in the trader callback thread."""
        self._logger.info(f"Message to be pushed: {xt_message}")

        asyncio.run_coroutine_threadsafe(
            self.notify_subscribers(xt_message),
            self._loop
        )

    def push_quote_update(self, datetime: dt.datetime, quote: dict[str, typing.Any]):
        """Push quote updates to message queue. This is the one that will be called in the quote callback thread.

        Args:
            datetime (dt.datetime): The time when the quotes were received.
            quote (dict[str, typing.Any]): The quote to be pushed.
        """
        asyncio.run_coroutine_threadsafe(
            self.push_quote_update_async(datetime, quote),
            self._loop
        )

    async def push_quote_update_async(self, datetime: dt.datetime, quote: dict[str, typing.Any]):
        now_ms = time.time() * 1000
        # Assuming all quotes have the same timestamp, take the first one
        latency = now_ms - quote['time']
        self._logger.info(
            f"Quote {quote['stock_code']} to be pushed. Received at {datetime.isoformat()}. Latency: {latency:.2f}ms")

    async def notify_subscribers(self, xt_message: message.XtMessage):
        # Record stats before notifying subscribers
        await self._record_stats(xt_message)

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

    async def _record_stats(self, xt_message: message.XtMessage):
        """Record statistics based on message type."""
        msg_type = xt_message.type
        msg_content = xt_message.message

        if msg_type == message.MessageType.STOCK_ORDER and msg_content is not None:
            # Only XtOrder has order_id and order_status
            if isinstance(msg_content, trade.XtOrder):
                self._stats_service.record_order_state_time(
                    msg_content.order_id, msg_content.order_status)

        elif msg_type == message.MessageType.ORDER_STOCK_ASYNC_RESPONSE and msg_content is not None:
            # Only XtOrderResponse has seq and order_id
            if isinstance(msg_content, trade.XtOrderResponse):
                self._stats_service.record_order_response_time(
                    msg_content.seq, msg_content.order_id)
