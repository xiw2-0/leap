from leap.models import trade
from leap.services import broker, stats_service, export_reader


class TradeService(object):
    def __init__(self) -> None:
        self._broker = broker.XtBroker()
        self._export_reader = export_reader.ExportReader()

        self._stats_service = stats_service.StatsService()

    def submit_stock_order_async(self, order_request: trade.OrderStockRequest) -> int:
        seq = self._broker.order_stock_async(order_request)
        self._stats_service.record_order_request_time(seq)
        return seq

    def cancel_stock_order_async(self, order_id: int) -> int:
        return self._broker.cancel_order_stock_async(order_id)

    def query_stock_orders(self) -> list[trade.XtOrder]:
        return self._broker.query_stock_orders()

    def query_stock_trades(self) -> list[trade.XtTrade]:
        return self._broker.query_stock_trades()

    def query_ipo_listing(self) -> list[trade.IPOListing]:
        return self._broker.query_ipo_listing()

    def query_ipo_purchase_limit(self) -> list[trade.NewStockPurchaseLimit]:
        return self._broker.query_new_stock_purchase_limit()

    def query_ipo_subscription_result(self):
        return self._export_reader.read_ipo_lucky_info()

    def query_ipo_subscription_number(self):
        return self._export_reader.read_subscrib_number()
