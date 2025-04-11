import fastapi

from leap.models import trade
from leap.services import trade_service

router = fastapi.APIRouter()


@router.post("/orders", response_model=int, summary="Submit stock order async", response_description="Order request id")
async def submit_stock_order_async(order_request: trade.OrderStockRequest) -> int:
    return await trade_service.TradeService().submit_stock_order_async(order_request)


@router.delete("/orders/{order_id}", response_model=int, summary="Cancel stock order async", response_description="Cancel order request id")
async def cancel_stock_order_async(order_id: int) -> int:
    return await trade_service.TradeService().cancel_stock_order_async(order_id)


@router.get("/orders", response_model=list[trade.XtOrder])
async def query_stock_orders_async() -> list[trade.XtOrder]:
    return await trade_service.TradeService().query_stock_orders_async()


@router.get("/trades", response_model=list[trade.XtTrade])
async def query_stock_trades_async() -> list[trade.XtTrade]:
    return await trade_service.TradeService().query_stock_trades_async()


@router.get("/ipo/listing", response_model=list[trade.IPOListing])
async def query_ipo_listing_async() -> list[trade.IPOListing]:
    return await trade_service.TradeService().query_ipo_listing_async()


@router.get("/ipo/purchase_limit", response_model=list[trade.NewStockPurchaseLimit])
async def query_ipo_purchase_limit_async() -> list[trade.NewStockPurchaseLimit]:
    return await trade_service.TradeService().query_ipo_purchase_limit_async()
