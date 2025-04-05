import unittest

from fastapi import testclient
from leap import main

client = testclient.TestClient(main.app)


class TestAsset(unittest.TestCase):
    def test_get_asset(self):
        response = client.get("/asset")
        assert response.status_code == 200


if __name__ == "__main__":
    unittest.main()
