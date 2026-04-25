import typing
import unittest

from unittest.mock import patch
from fastapi import testclient
from leap.models import asset


class TestAsset(unittest.IsolatedAsyncioTestCase):
    @patch('leap.services.broker.XtBroker')
    # Mock logging setup to avoid path issues
    @patch('leap.utils.logging_config.setup_logging')
    async def test_get_asset(self, mock_logging: typing.Any, mock_xtbroker: typing.Any) -> None:
        # Configure the mock instance
        mock_instance = mock_xtbroker.return_value
        mock_instance.query_stock_asset.return_value = asset.XtAsset(
            account_id="123456",
            account_type=1,
            cash=5000,
            frozen_cash=0,
            market_value=0,
            total_asset=10000,
        )

        # Import after patching logging setup to avoid path errors
        import leap.main
        with testclient.TestClient(leap.main.app, raise_server_exceptions=True) as client:
            # Call the correct endpoint with prefix: /asset/account
            response = client.get("/asset/account")
            assert response.status_code == 200
            assert response.json() == {
                'account_type': 1, 'account_id': '123456', 'cash': 5000.0,
                'frozen_cash': 0.0, 'market_value': 0.0, 'total_asset': 10000.0
            }


if __name__ == "__main__":
    unittest.main()
