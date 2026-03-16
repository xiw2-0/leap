import fastapi

from leap.models import trade
from leap.services import trade_service

router = fastapi.APIRouter()


@router.post("/orders/async", response_model=int, summary="Submit stock order async", response_description="Order request id")
async def submit_stock_order_async(order_request: trade.OrderStockRequest) -> int:
    return trade_service.TradeService().submit_stock_order_async(order_request)


@router.post("/orders/sync", response_model=int, summary="Submit stock order sync", response_description="Order ID (positive for success, -1 for failure)")
def submit_stock_order_sync(order_request: trade.OrderStockRequest) -> int:
    return trade_service.TradeService().submit_stock_order_sync(order_request)


@router.delete("/orders/{order_id}/async", response_model=int, summary="Cancel stock order async", response_description="Cancel order request id")
async def cancel_stock_order_async(order_id: int) -> int:
    return trade_service.TradeService().cancel_stock_order_async(order_id)


@router.delete("/orders/{order_id}/sync", response_model=int, summary="Cancel stock order sync", response_description="0 for success, -1 for failure")
def cancel_stock_order_sync(order_id: int) -> int:
    return trade_service.TradeService().cancel_stock_order_sync(order_id)


@router.get("/orders", response_model=list[trade.XtOrder])
async def query_stock_orders() -> list[trade.XtOrder]:
    return trade_service.TradeService().query_stock_orders()


@router.get("/trades", response_model=list[trade.XtTrade])
async def query_stock_trades() -> list[trade.XtTrade]:
    return trade_service.TradeService().query_stock_trades()


@router.get("/ipo/listing", response_model=list[trade.IPOListing])
async def query_ipo_listing() -> list[trade.IPOListing]:
    return trade_service.TradeService().query_ipo_listing()


@router.get("/ipo/purchase_limit", response_model=list[trade.NewStockPurchaseLimit])
async def query_ipo_purchase_limit() -> list[trade.NewStockPurchaseLimit]:
    return trade_service.TradeService().query_ipo_purchase_limit()


@router.get("/ipo/subscription_number", response_model=list[trade.IPOSubscriptionNumber])
def query_ipo_subscription_number():
    return trade_service.TradeService().query_ipo_subscription_number()


@router.get("/ipo/subscription_result", response_model=list[trade.IPOSubscriptionResult])
def query_ipo_subscription_result():
    return trade_service.TradeService().query_ipo_subscription_result()
