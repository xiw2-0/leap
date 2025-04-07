import fastapi

from leap.models import asset
from leap.services import asset_service

router = fastapi.APIRouter()


@router.get("/account", response_model=asset.XtAsset)
async def get_asset_async():
    return await asset_service.AssetService().get_account_asset_async()


@router.get("/positions", response_model=list[asset.XtPosition], summary="Get positions async")
async def get_positions_async():
    return await asset_service.AssetService().get_positions_async()


# TODO: 同步接口的并发是通过多线程，所以需要考虑加锁。
@router.get("/positions/stocks/{stock}", response_model=asset.XtPosition, summary="Get position by stock code")
def get_position(stock: str):
    return asset_service.AssetService().get_position(stock)
