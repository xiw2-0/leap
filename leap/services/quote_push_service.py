import asyncio
import datetime as dt
import logging
import time
import typing

import fastapi

from leap.models import message
from leap.models.quote import Tick
from leap.services import stats_service, quote_subscriber
from leap.utils import singleton


@singleton.singleton
class QuotePushService(object):

    def __init__(self) -> None:
        # Store quote subscriptions - mapping stock codes to WebSocket connections interested in those stocks
        self._quote_subscriptions: dict[str, list[fastapi.WebSocket]] = {}

        self._logger = logging.getLogger(__name__)
        self._stats_service = stats_service.StatsService()

    def init(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._logger.info("Event loop set for QuotePushService")

    def subscribe_to_quotes(self, websocket: fastapi.WebSocket, stock_codes: list[str]) -> list[str]:
        """Subscribe a websocket connection to quote updates for specific stock codes."""
        subscribed_codes: list[str] = []
        for stock_code in stock_codes:
            if stock_code not in self._quote_subscriptions:
                if not quote_subscriber.QuoteSubscriber().subscribe(stock_code):
                    self._logger.error(
                        f"Failed to subscribe to quote for {stock_code}")
                    continue
                self._quote_subscriptions[stock_code] = []
            if websocket not in self._quote_subscriptions[stock_code]:
                self._quote_subscriptions[stock_code].append(websocket)
            subscribed_codes.append(stock_code)
        self._logger.info(
            f"WebSocket {websocket.client} subscribed to quote updates for {subscribed_codes}. "
            f"Total quote subscribers for {stock_codes}: {[len(self._quote_subscriptions.get(code, [])) for code in stock_codes]}")
        return subscribed_codes

    def unsubscribe_from_quotes(self, websocket: fastapi.WebSocket, stock_codes: list[str]) -> None:
        """Unsubscribe a websocket connection from quote updates for specific stock codes.

        If stock_codes is empty, unsubscribe from all quote updates.
        """
        if len(stock_codes) == 0:
            # Unsubscribe from all stock codes for this websocket
            for stock_code in list(self._quote_subscriptions.keys()):
                if websocket in self._quote_subscriptions[stock_code]:
                    self._quote_subscriptions[stock_code].remove(websocket)
                    # Clean up empty lists
                    if not self._quote_subscriptions[stock_code]:
                        quote_subscriber.QuoteSubscriber().unsubscribe(stock_code)
                        del self._quote_subscriptions[stock_code]
            self._logger.info(
                f"WebSocket {websocket.client} unsubscribed from all quote updates")
        else:
            # Unsubscribe from specific stock codes
            for stock_code in stock_codes:
                if stock_code in self._quote_subscriptions and websocket in self._quote_subscriptions[stock_code]:
                    self._quote_subscriptions[stock_code].remove(websocket)
                    # Clean up empty lists
                    if not self._quote_subscriptions[stock_code]:
                        quote_subscriber.QuoteSubscriber().unsubscribe(stock_code)
                        del self._quote_subscriptions[stock_code]
            self._logger.info(
                f"WebSocket {websocket.client} unsubscribed from quote updates for {stock_codes}")

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
        stock_code = quote['stock_code']

        # Record stats before notifying subscribers
        self._stats_service.record_data_delay([latency])

        # Get the subscribers for this specific stock code
        subscribers = self._quote_subscriptions.get(stock_code, [])
        if not subscribers:
            self._logger.info(
                f"No active WebSocket connections for quote {stock_code}.")
            return

        tick = Tick(
            stock_code=stock_code,
            time=quote['time'],
            last_price=quote['lastPrice'],
            open=quote['open'],
            high=quote['high'],
            low=quote['low'],
            last_close=quote["lastClose"],
            amount=quote["amount"],
            volume=quote["volume"],
            pvolume=quote["pvolume"],
            stock_status=quote["stockStatus"],
            open_int=quote["openInt"],
            last_settlement_price=quote["lastSettlementPrice"],
            ask_prices=quote["askPrice"],
            bid_prices=quote["bidPrice"],
            ask_vols=quote["askVol"],
            bid_vols=quote["bidVol"],
        )
        quote_update = message.XtMessage(
            message=tick,
            timestamp=datetime,
            type=message.MessageType.QUOTE_UPDATE
        ).model_dump_json()
        remove_list: list[fastapi.WebSocket] = []
        for connection in subscribers:
            try:
                await connection.send_text(quote_update)
                self._logger.info(
                    f"Quote sent to {connection.client}: {stock_code}. Latency: {latency:.2f}ms")
            except Exception as e:
                self._logger.error(
                    f"Error sending quote to client: {e}. Closing connection. Application state: {connection.application_state}. Client state: {connection.client_state}.")
                remove_list.append(connection)

        for conn in remove_list:
            if stock_code in self._quote_subscriptions and conn in self._quote_subscriptions[stock_code]:
                self._quote_subscriptions[stock_code].remove(conn)
                # Clean up empty lists
                if not self._quote_subscriptions[stock_code]:
                    quote_subscriber.QuoteSubscriber().unsubscribe(stock_code)
                    del self._quote_subscriptions[stock_code]
