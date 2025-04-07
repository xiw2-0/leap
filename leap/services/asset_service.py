from leap.models import asset
from leap.services import broker


class AssetService(object):

    def __init__(self) -> None:
        self._broker = broker.XtBroker()

    async def get_account_asset_async(self) -> asset.XtAsset:
        return await self._broker.query_stock_asset_async()

    async def get_positions_async(self) -> list[asset.XtPosition]:
        return await self._broker.query_stock_positions_async()

    def get_position(self, stock_code: str) -> asset.XtPosition:
        return self._broker.query_stock_position(stock_code)
        
