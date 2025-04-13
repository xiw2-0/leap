import datetime as dt
import enum
import pydantic

from leap.models import account, trade, asset


class MessageType(enum.Enum):
    DISCONNECTED = 'DISCONNECTED'
    STOCK_ORDER = 'STOCK_ORDER'
    STOCK_TRADE = 'STOCK_TRADE'
    STOCK_ASSET = 'STOCK_ASSET'
    STOCK_POSITION = 'STOCK_POSITION'
    ORDER_ERROR = 'ORDER_ERROR'
    CANCEL_ERROR = 'CANCEL_ERROR'
    ORDER_STOCK_ASYNC_RESPONSE = 'ORDER_STOCK_ASYNC_RESPONSE'
    CANCEL_ORDER_STOCK_ASYNC_RESPONSE = 'CANCEL_ORDER_STOCK_ASYNC_RESPONSE'
    ACCOUNT_STATUS = 'ACCOUNT_STATUS'


class XtMessage(pydantic.BaseModel):
    type: MessageType
    timestamp: dt.datetime

    message: account.XtAccountStatus | trade.XtOrder | trade.XtTrade | asset.XtAsset | asset.XtPosition | trade.XtOrderError | trade.XtCancelError | trade.XtOrderResponse | trade.XtCancelOrderResponse | None
