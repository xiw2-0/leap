from leap.models import trade
from leap.services import broker


class TradeService(object):
    def __init__(self) -> None:
        self._broker = broker.XtBroker()

    async def submit_stock_order_async(self, order_request: trade.OrderStockRequest) -> int:
        return await self._broker.order_stock_async(order_request)

    async def cancel_stock_order_async(self, order_id: int) -> int:
        return await self._broker.cancel_order_stock_async(order_id)

    async def query_stock_orders_async(self) -> list[trade.XtOrder]:
        return await self._broker.query_stock_orders_async()

    async def query_stock_trades_async(self) -> list[trade.XtTrade]:
        return await self._broker.query_stock_trades_async()

    async def query_ipo_listing_async(self) -> list[trade.IPOListing]:
        return await self._broker.query_ipo_listing_async()

    async def query_ipo_purchase_limit_async(self) -> list[trade.NewStockPurchaseLimit]:
        return await self._broker.query_new_stock_purchase_limit_sync()
