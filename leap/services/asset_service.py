from leap.models import asset
from leap.services import broker


class AssetService(object):

    def __init__(self) -> None:
        self._broker = broker.XtBroker()

    def get_account_asset(self) -> asset.XtAsset:
        return self._broker.query_stock_asset()

    def get_positions(self) -> list[asset.XtPosition]:
        return self._broker.query_stock_positions()

    def get_position(self, stock_code: str) -> asset.XtPosition:
        return self._broker.query_stock_position(stock_code)
        
