import fastapi

from leap.models import trade
from leap.services import trade_service

router = fastapi.APIRouter()


@router.post("/orders", response_model=int, summary="Submit stock order async", response_description="Order request id")
async def submit_stock_order_async(order_request: trade.OrderStockRequest) -> int:
    return await trade_service.TradeService().submit_stock_order_async(order_request)
