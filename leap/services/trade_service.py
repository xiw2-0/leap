from leap.models import trade
from leap.services import broker


class TradeService(object):
    def __init__(self) -> None:
        self._broker = broker.XtBroker()

    async def submit_stock_order_async(self, order_request: trade.OrderStockRequest) -> int:
        return await self._broker.order_stock_async(order_request)

    async def cancel_stock_order_async(self, order_id: int) -> int:
        return await self._broker.cancel_order_stock_async(order_id)

    def query_stock_orders(self) -> list[trade.XtOrder]:
        return self._broker.query_stock_orders()

    def query_stock_trades(self) -> list[trade.XtTrade]:
        return self._broker.query_stock_trades()

    def query_ipo_listing(self) -> list[trade.IPOListing]:
        return self._broker.query_ipo_listing()

    def query_ipo_purchase_limit(self) -> list[trade.NewStockPurchaseLimit]:
        return self._broker.query_new_stock_purchase_limit()
