import fastapi

from leap.services import stats_service

router = fastapi.APIRouter()


@router.get("/ping", summary="Test Network Delay")
def get_ping_delay():
    return "pong"


@router.get("/api", summary="Get API Delay Stats")
def get_api_stats():
    return stats_service.StatsService().get_api_stats()


@router.get("/order", summary="Get Order Delay Stats")
def get_order_stats():
    return stats_service.StatsService().get_order_stats()