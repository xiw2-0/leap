import fastapi

from leap.models import asset
from leap.services import asset_service

router = fastapi.APIRouter()


@router.get("/", response_model=asset.XtAsset)
async def get_asset():
    return await asset_service.AssetService().get_asset()
