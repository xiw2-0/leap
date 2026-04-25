import fastapi

from leap.models import asset
from leap.services import asset_service

router = fastapi.APIRouter()


@router.get("/account", response_model=asset.XtAsset, summary="Get account asset")
async def get_asset(request: fastapi.Request):
    svc: asset_service.AssetService = request.state.asset_service
    return svc.get_account_asset()


@router.get("/positions", response_model=list[asset.XtPosition], summary="Get positions")
async def get_positions(request: fastapi.Request):
    svc: asset_service.AssetService = request.state.asset_service
    return svc.get_positions()


@router.get("/positions/stocks/{stock}", response_model=asset.XtPosition, summary="Get position by stock code")
async def get_position(stock: str, request: fastapi.Request):
    svc: asset_service.AssetService = request.state.asset_service
    return svc.get_position(stock)
