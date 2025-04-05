import fastapi

from leap.models import asset
from leap.services import asset_service

router = fastapi.APIRouter()


@router.get("/", response_model=asset.XtAsset)
def get_user():
    return asset_service.get_asset()
