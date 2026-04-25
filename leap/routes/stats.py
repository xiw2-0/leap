import fastapi

router = fastapi.APIRouter()


@router.get("/ping", summary="Test Network Delay")
async def get_ping_delay():
    return "pong"


@router.get("/api", summary="Get API Delay Stats")
async def get_api_stats(request: fastapi.Request):
    return request.state.stats_service.get_api_stats()


@router.get("/order", summary="Get Order Delay Stats")
async def get_order_stats(request: fastapi.Request):
    return request.state.stats_service.get_order_stats()


@router.get("/data", summary="Get Data Delay Stats")
async def get_data_stats(request: fastapi.Request):
    return request.state.stats_service.get_data_stats()


@router.delete("/api", summary="Clear API Delay Stats")
async def clear_api_stats(request: fastapi.Request):
    request.state.stats_service.clear_api_stats()
    return {"message": "API Statistics cleared successfully"}


@router.delete("/order", summary="Clear Order Delay Stats")
async def clear_order_stats(request: fastapi.Request):
    request.state.stats_service.clear_order_stats()
    return {"message": "Order Statistics cleared successfully"}


@router.delete("/data", summary="Clear Data Delay Stats")
async def clear_data_stats(request: fastapi.Request):
    request.state.stats_service.clear_data_stats()
    return {"message": "Data Statistics cleared successfully"}


@router.delete("/all", summary="Clear All Stats Data")
async def clear_all_stats(request: fastapi.Request):
    request.state.stats_service.clear_stats()
    return {"message": "All Statistics cleared successfully"}
