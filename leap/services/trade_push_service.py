import asyncio
import logging

import fastapi

from leap.models import message, trade
from leap.services import stats_service
from leap.utils import singleton


@singleton.singleton
class TradePushService(object):

    def __init__(self) -> None:
        # Store trade subscriptions - WebSocket connections interested in trade updates
        self._trade_subscriptions: list[fastapi.WebSocket] = []

        self._logger = logging.getLogger(__name__)
        self._stats_service = stats_service.StatsService()

    def init(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._logger.info("Event loop set for TradePushService")

    def subscribe_to_trade(self, websocket: fastapi.WebSocket) -> None:
        """Subscribe a websocket connection to trade updates."""
        if websocket not in self._trade_subscriptions:
            self._trade_subscriptions.append(websocket)
            self._logger.info(
                f"WebSocket {websocket.client} subscribed to trade updates. "
                f"Total trade subscribers: {len(self._trade_subscriptions)}")

    def unsubscribe_from_trade(self, websocket: fastapi.WebSocket) -> None:
        """Unsubscribe a websocket connection from trade updates."""
        if websocket in self._trade_subscriptions:
            self._trade_subscriptions.remove(websocket)
            self._logger.info(
                f"WebSocket {websocket.client} unsubscribed from trade updates. "
                f"Total trade subscribers: {len(self._trade_subscriptions)}")

    def push_trade_message(self, xt_message: message.XtMessage):
        """Push the message to message queue. This is the one that will be called in the trader callback thread."""
        self._logger.info(f"Trade message to be pushed: {xt_message}")

        asyncio.run_coroutine_threadsafe(
            self.notify_trade_subscribers(xt_message),
            self._loop
        )

    async def notify_trade_subscribers(self, xt_message: message.XtMessage):
        # Record stats before notifying subscribers
        await self._record_stats(xt_message)

        if not self._trade_subscriptions:
            self._logger.info(
                "No active WebSocket connections to push trade message to.")
            return

        remove_list: list[fastapi.WebSocket] = []
        for connection in self._trade_subscriptions:
            try:
                await connection.send_text(xt_message.model_dump_json())
                self._logger.info(
                    f"Trade message sent to {connection.client}: {xt_message.type}")
            except Exception as e:
                self._logger.error(
                    f"Error sending trade message to client: {e}. Closing connection. Application state: {connection.application_state}. Client state: {connection.client_state}.")
                remove_list.append(connection)
        for conn in remove_list:
            if conn in self._trade_subscriptions:
                self._trade_subscriptions.remove(conn)

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
