from leap.models import trade
from leap.services import broker


class TradeService(object):
    def __init__(self) -> None:
        self._broker = broker.XtBroker()

    async def submit_stock_order_async(self, order_request: trade.OrderStockRequest) -> int:
        return await self._broker.order_stock_async(order_request)