import logging

from leap.models import trade
from leap.services import broker, stats_service, export_reader


logger = logging.getLogger(__name__)


class TradeService(object):
    def __init__(self) -> None:
        self._broker = broker.XtBroker()
        self._export_reader = export_reader.ExportReader()

        self._stats_service = stats_service.StatsService()

    def submit_stock_order_async(self, order_request: trade.OrderStockRequest) -> int:
        logger.info(
            f"Submitting stock order async: {order_request.model_dump()}")
        seq = self._broker.order_stock_async(order_request)
        self._stats_service.record_order_request_time(seq, None)
        logger.info(f"Order submitted successfully. Sequence: {seq}")
        return seq

    def submit_stock_order_sync(self, order_request: trade.OrderStockRequest) -> int:
        """Sync version that returns order_id (positive for success, -1 for failure)"""
        logger.info(
            f"Submitting stock order sync: {order_request.model_dump()}")
        order_id = self._broker.order_stock_sync(order_request)
        self._stats_service.record_order_request_time(None, order_id)
        logger.info(f"Sync order submitted successfully. Order ID: {order_id}")
        return order_id

    def cancel_stock_order_async(self, order_id: int) -> int:
        logger.info(f"Canceling stock order: order_id={order_id}")
        result = self._broker.cancel_order_stock_async(order_id)
        logger.info(f"Cancel order result: {result}")
        return result

    def cancel_stock_order_sync(self, order_id: int) -> int:
        """Sync version that returns 0 for success, -1 for failure"""
        logger.info(f"Canceling stock order sync: order_id={order_id}")
        result = self._broker.cancel_order_stock_sync(order_id)
        logger.info(
            f"Sync cancel order, order ID: {order_id}, result: {result}")
        return result

    def query_stock_orders(self) -> list[trade.XtOrder]:
        logger.info("Querying stock orders")
        orders = self._broker.query_stock_orders()
        logger.info(
            f"Retrieved stock orders: {[order.model_dump() for order in orders]}")
        return orders

    def query_stock_trades(self) -> list[trade.XtTrade]:
        logger.info("Querying stock trades")
        trades = self._broker.query_stock_trades()
        logger.info(
            f"Retrieved stock trades: {[trade.model_dump() for trade in trades]}")
        return trades

    def query_ipo_listing(self) -> list[trade.IPOListing]:
        logger.info("Querying IPO listings")
        listings = self._broker.query_ipo_listing()
        logger.info(
            f"Retrieved IPO listings: {[listing.model_dump() for listing in listings]}")
        return listings

    def query_ipo_purchase_limit(self) -> list[trade.NewStockPurchaseLimit]:
        logger.info("Querying IPO purchase limits")
        limits = self._broker.query_new_stock_purchase_limit()
        logger.info(
            f"Retrieved IPO purchase limits: {[limit.model_dump() for limit in limits]}")
        return limits

    def query_ipo_subscription_result(self):
        logger.info("Querying IPO subscription results")
        result = self._export_reader.read_ipo_lucky_info()
        logger.info(f"IPO subscription result retrieved: {result}")
        return result

    def query_ipo_subscription_number(self):
        logger.info("Querying IPO subscription numbers")
        result = self._export_reader.read_subscrib_number()
        logger.info(f"IPO subscription numbers retrieved: {result}")
        return result
