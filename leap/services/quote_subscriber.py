import logging
import typing
import datetime as dt
from xtquant import xtdata  # type: ignore

from leap.services.push_service import PushService
from leap.utils import singleton


@singleton.singleton
class QuoteSubscriber(object):
    """
    Service to handle subscribing and unsubscribing to individual stock quotes from xtdata
    and forwarding them to the push service for WebSocket distribution.
    """

    def __init__(self) -> None:
        self._push_service = PushService()
        # Dictionary to map stock codes to subscription IDs
        self._subscriptions: dict[str, int] = {}

        self._tz = dt.timezone(dt.timedelta(hours=8))
        self._logger = logging.getLogger(__name__)

    def subscribe(self, stock_code: str) -> bool:
        """
        Subscribe to quotes for a specific stock.

        Args:
            stock_code: The stock code to subscribe to (e.g., '000001.SZ')

        Returns:
            True if subscription was successful, False otherwise
        """
        if stock_code in self._subscriptions:
            self._logger.info(f"Already subscribed to {stock_code}")
            return True

        # Subscribe to the specific stock and store the subscription ID
        sub_id = int(xtdata.subscribe_quote(  # type: ignore
            stock_code,
            period='tick',
            callback=self._on_quote_update
        ))

        # Check if subscription was successful
        if sub_id != 0:
            self._subscriptions[stock_code] = int(sub_id)
            self._logger.info(
                f"Successfully subscribed to {stock_code}, subscription ID: {sub_id}")
            return True

        return False

    def unsubscribe(self, stock_code: str) -> None:
        """
        Unsubscribe from quotes for a specific stock.

        Args:
            stock_code: The stock code to unsubscribe from
        """
        if stock_code not in self._subscriptions:
            self._logger.info(f"Not subscribed to {stock_code}")
            return

        # Get the subscription ID for this stock
        sub_id = self._subscriptions[stock_code]

        # Unsubscribe using the subscription ID
        xtdata.unsubscribe_quote(sub_id)  # type: ignore

        # Remove from our tracking
        del self._subscriptions[stock_code]
        self._logger.info(
            f"Unsubscribed from {stock_code}, subscription ID: {sub_id}")

    def _on_quote_update(self, data: dict[str, list[dict[str, typing.Any]]]) -> None:
        """
        Callback function that gets called when new quote data arrives from xtdata.
        Forwards to push service immediately.

        Args:
            data: Dictionary containing the quote data from xtdata
        """
        for stock_code, quotes in data.items():
            self._logger.info(f"Received quote update for {stock_code}")
            for quote in quotes:
                self._push_service.push_quote_update(
                    dt.datetime.now(self._tz), quote)
