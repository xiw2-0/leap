import datetime as dt

from leap.models import account, message
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

    def _datetime_now(self) -> dt.datetime:
        return dt.datetime.now(tz=self._tz)
