import typing
import unittest
import unittest.mock

from fastapi import testclient
from leap import main
from leap.models import asset
from unittest.mock import patch

client = testclient.TestClient(main.app)


class TestAsset(unittest.IsolatedAsyncioTestCase):
    @patch('leap.services.broker.XtBroker')
    async def test_get_asset(self, mock_xtbroker: typing.Any):
        mock_instance = mock_xtbroker.return_value
        mock_instance.query_stock_asset_async = unittest.mock.AsyncMock(return_value=asset.XtAsset(
            account_id="123456",
            account_type=1,
            cash=5000,
            frozen_cash=0,
            market_value=0,
            total_asset=10000,
        ))

        response = client.get("/asset")
        assert response.status_code == 200
        assert response.json() == {
            'account_type': 1, 'account_id': '123456', 'cash': 5000.0,
            'frozen_cash': 0.0, 'market_value': 0.0, 'total_asset': 10000.0
        }


if __name__ == "__main__":
    unittest.main()
