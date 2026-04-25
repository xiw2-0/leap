import logging

from leap.models import asset
from leap.services import broker


logger = logging.getLogger(__name__)


class AssetService(object):

    def __init__(self, broker: broker.XtBroker) -> None:
        self._broker = broker

    def get_account_asset(self) -> asset.XtAsset:
        logger.info("Querying account asset")
        result = self._broker.query_stock_asset()
        logger.info(f"Account asset retrieved: {result.model_dump()}")
        return result

    def get_positions(self) -> list[asset.XtPosition]:
        logger.info("Querying all positions")
        result = self._broker.query_stock_positions()
        logger.info(f"Retrieved positions: {[pos.model_dump() for pos in result]}")
        return result

    def get_position(self, stock_code: str) -> asset.XtPosition:
        logger.info(f"Querying position for stock: {stock_code}")
        result = self._broker.query_stock_position(stock_code)
        logger.info(f"Position for {stock_code} retrieved: {result.model_dump()}")
        return result