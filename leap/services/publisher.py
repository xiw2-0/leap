import datetime as dt

from leap.models import account, message, trade
from leap.services import push_service
from leap.utils import model_util
from xtquant import xttype, xttrader  # type: ignore


class XtPublisher(xttrader.XtQuantTraderCallback):
    """XT Trader status publisher."""

    def __init__(self) -> None:
        self._push_service = push_service.PushService()

        self._tz = dt.timezone(dt.timedelta(hours=8))

    def on_disconnected(self):
        self._push_service.notify_subscribers(message.XtMessage(
            type=message.MessageType.DISCONNECTED,
            timestamp=self._datetime_now(),
            message=None))

    def on_account_status(self, status: xttype.XtAccountStatus):
        self._push_service.notify_subscribers(message.XtMessage(
            type=message.MessageType.ACCOUNT_STATUS,
            timestamp=self._datetime_now(),
            message=model_util.to_pydantic_model(
                status, account.XtAccountStatus)
        ))

    def on_stock_order(self, order: xttype.XtOrder):
        self._push_service.notify_subscribers(message.XtMessage(
            type=message.MessageType.STOCK_ORDER,
            timestamp=self._datetime_now(),
            message=model_util.to_pydantic_model(
                order, trade.XtOrder)
        ))

    def on_stock_trade(self, xt_trade: xttype.XtTrade):
        self._push_service.notify_subscribers(message.XtMessage(
            type=message.MessageType.STOCK_TRADE,
            timestamp=self._datetime_now(),
            message=model_util.to_pydantic_model(
                xt_trade, trade.XtTrade)
        ))

    def on_order_error(self, order_error: xttype.XtOrderError):
        self._push_service.notify_subscribers(message.XtMessage(
            type=message.MessageType.ORDER_ERROR,
            timestamp=self._datetime_now(),
            message=model_util.to_pydantic_model(
                order_error, trade.XtOrderError)
        ))

    def on_cancel_error(self, cancel_error: xttype.XtCancelError):
        self._push_service.notify_subscribers(message.XtMessage(
            type=message.MessageType.CANCEL_ERROR,
            timestamp=self._datetime_now(),
            message=model_util.to_pydantic_model(
                cancel_error, trade.XtCancelError)
        ))

    def on_order_stock_async_response(self, response: xttype.XtOrderResponse):
        self._push_service.notify_subscribers(message.XtMessage(
            type=message.MessageType.ORDER_STOCK_ASYNC_RESPONSE,
            timestamp=self._datetime_now(),
            message=model_util.to_pydantic_model(
                response, trade.XtOrderResponse)
        ))

    def on_cancel_order_stock_async_response(self, response: xttype.XtCancelOrderResponse):
        self._push_service.notify_subscribers(message.XtMessage(
            type=message.MessageType.CANCEL_ORDER_STOCK_ASYNC_RESPONSE,
            timestamp=self._datetime_now(),
            message=model_util.to_pydantic_model(
                response, trade.XtCancelOrderResponse)
        ))

    def _datetime_now(self) -> dt.datetime:
        return dt.datetime.now(tz=self._tz)
