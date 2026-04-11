import logging
import typing
import datetime as dt
from xtquant import xtdata  # type: ignore

from leap.services.push_service import PushService
from leap.utils import singleton


@singleton.singleton
class QuoteSubscriber(object):
    """
    Service to handle subscribing and unsubscribing to whole market quotes from xtdata
    and forwarding them to the push service for WebSocket distribution.
    """

    def __init__(self) -> None:
        self._push_service = PushService()
        # Single subscription ID for both markets
        self._subscription_id: typing.Optional[int] = None

        self._tz = dt.timezone(dt.timedelta(hours=8))
        self._logger = logging.getLogger(__name__)

    def subscribe(self) -> None:
        """
        Subscribe to whole market quotes for all stocks in SH and SZ markets using a single subscription.
        """
        if self._subscription_id is not None:
            self._logger.info(
                f"Markets are already subscribed with subscription ID: {self._subscription_id}")
            return

        # Subscribe to whole market quotes for both SH and SZ markets
        # xtdata.subscribe_whole_quote returns a single subscription ID for both markets
        markets = ["SH", "SZ"]
        self._subscription_id = int(xtdata.subscribe_whole_quote(  # type: ignore
            markets,
            callback=self._on_quote_update
        ))

        self._logger.info(
            f"Subscribed to whole quotes for markets {markets}, subscription ID: {self._subscription_id}")

    def unsubscribe(self) -> None:
        """
        Unsubscribe from whole market quotes using the stored subscription ID.
        """
        if self._subscription_id is None:
            self._logger.info("No active subscription to unsubscribe")
            return

        # Unsubscribe using the subscription ID
        success = bool(xtdata.unsubscribe_quote(  # type: ignore
            self._subscription_id))
        self._logger.info(
            f"Unsubscribed from whole quotes for markets ['SH', 'SZ'], subscription ID: {self._subscription_id}, success: {success}")

        # Reset the subscription ID
        self._subscription_id = None

    def _on_quote_update(self, data: typing.Dict[str, typing.Any]) -> None:
        """
        Callback function that gets called when new quote data arrives from xtdata.
        Forwards to push service immediately.

        Args:
            data: Dictionary containing the quote data from xtdata
        """
        self._push_service.push_quote_updates(dt.datetime.now(self._tz), data)

