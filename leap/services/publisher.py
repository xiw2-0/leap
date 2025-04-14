import datetime as dt

from leap.models import account, message, trade as trade_model, asset as asset_model
from leap.services import push_service, stats_service
from leap.utils import model_util
from xtquant import xttype, xttrader  # type: ignore


class XtPublisher(xttrader.XtQuantTraderCallback):
    """XT Trader status publisher."""

    def __init__(self) -> None:
        self._push_service = push_service.PushService()
        self._stats_service = stats_service.StatsService()

        self._tz = dt.timezone(dt.timedelta(hours=8))

    def on_connected(self):
        pass

    def on_disconnected(self):
        self._push_service.push_message(message.XtMessage(
            type=message.MessageType.DISCONNECTED,
            timestamp=self._datetime_now(),
            message=None))

    def on_account_status(self, status: xttype.XtAccountStatus):
        self._push_service.push_message(message.XtMessage(
            type=message.MessageType.ACCOUNT_STATUS,
            timestamp=self._datetime_now(),
            message=model_util.pydantic_model_from_object(
                status, account.XtAccountStatus)
        ))

    def on_stock_asset(self, asset: xttype.XtAsset):
        self._push_service.push_message(message.XtMessage(
            type=message.MessageType.STOCK_ASSET,
            timestamp=self._datetime_now(),
            message=model_util.pydantic_model_from_object(
                asset, asset_model.XtAsset)
        ))

    def on_stock_position(self, position: xttype.XtPosition):
        self._push_service.push_message(message.XtMessage(
            type=message.MessageType.STOCK_POSITION,
            timestamp=self._datetime_now(),
            message=model_util.pydantic_model_from_object(
                position, asset_model.XtPosition)
        ))

    def on_stock_order(self, order: xttype.XtOrder):
        self._stats_service.record_order_state_time(
            order.order_id, order.order_status)  # type: ignore
        self._push_service.push_message(message.XtMessage(
            type=message.MessageType.STOCK_ORDER,
            timestamp=self._datetime_now(),
            message=model_util.pydantic_model_from_object(
                order, trade_model.XtOrder)
        ))

    def on_stock_trade(self, trade: xttype.XtTrade):
        self._push_service.push_message(message.XtMessage(
            type=message.MessageType.STOCK_TRADE,
            timestamp=self._datetime_now(),
            message=model_util.pydantic_model_from_object(
                trade, trade_model.XtTrade)
        ))

    def on_order_error(self, order_error: xttype.XtOrderError):
        self._push_service.push_message(message.XtMessage(
            type=message.MessageType.ORDER_ERROR,
            timestamp=self._datetime_now(),
            message=model_util.pydantic_model_from_object(
                order_error, trade_model.XtOrderError)
        ))

    def on_cancel_error(self, cancel_error: xttype.XtCancelError):
        self._push_service.push_message(message.XtMessage(
            type=message.MessageType.CANCEL_ERROR,
            timestamp=self._datetime_now(),
            message=model_util.pydantic_model_from_object(
                cancel_error, trade_model.XtCancelError)
        ))

    def on_order_stock_async_response(self, response: xttype.XtOrderResponse):
        self._stats_service.record_order_response_time(
            response.seq, response.order_id)  # type: ignore
        self._push_service.push_message(message.XtMessage(
            type=message.MessageType.ORDER_STOCK_ASYNC_RESPONSE,
            timestamp=self._datetime_now(),
            message=model_util.pydantic_model_from_object(
                response, trade_model.XtOrderResponse)
        ))

    def on_cancel_order_stock_async_response(self, response: xttype.XtCancelOrderResponse):
        self._push_service.push_message(message.XtMessage(
            type=message.MessageType.CANCEL_ORDER_STOCK_ASYNC_RESPONSE,
            timestamp=self._datetime_now(),
            message=model_util.pydantic_model_from_object(
                response, trade_model.XtCancelOrderResponse)
        ))

    def on_smt_appointment_async_response(self, response: xttype.XtSmtAppointmentResponse):
        pass

    def _datetime_now(self) -> dt.datetime:
        return dt.datetime.now(tz=self._tz)
