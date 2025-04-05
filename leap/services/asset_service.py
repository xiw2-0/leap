from leap.models import asset


def get_asset() -> asset.XtAsset:
    return asset.XtAsset(account_id="123", account_type=1, cash=100, frozen_cash=0, market_value=100, total_asset=100)
