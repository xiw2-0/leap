from leap.models import asset
from leap.services import broker


class AssetService(object):

    def __init__(self) -> None:
        self._broker = broker.XtBroker()

    async def get_asset(self) -> asset.XtAsset:
        return await self._broker.query_stock_asset_async()
