import fastapi

from leap.services import stats_service

router = fastapi.APIRouter()


@router.get("/ping", summary="Test Network Delay")
async def get_ping_delay():
    return "pong"


@router.get("/api", summary="Get API Delay Stats")
async def get_api_stats():
    return stats_service.StatsService().get_api_stats()


@router.get("/order", summary="Get Order Delay Stats")
async def get_order_stats():
    return stats_service.StatsService().get_order_stats()


@router.get("/data", summary="Get Data Delay Stats")
async def get_data_stats():
    return stats_service.StatsService().get_data_stats()


@router.delete("/api", summary="Clear API Delay Stats")
async def clear_api_stats():
    stats_service.StatsService().clear_api_stats()
    return {"message": "API Statistics cleared successfully"}


@router.delete("/order", summary="Clear Order Delay Stats")
async def clear_order_stats():
    stats_service.StatsService().clear_order_stats()
    return {"message": "Order Statistics cleared successfully"}


@router.delete("/data", summary="Clear Data Delay Stats")
async def clear_data_stats():
    stats_service.StatsService().clear_data_stats()
    return {"message": "Data Statistics cleared successfully"}


@router.delete("/all", summary="Clear All Stats Data")
async def clear_all_stats():
    stats_service.StatsService().clear_stats()
    return {"message": "All Statistics cleared successfully"}
