import pydantic


class XtAsset(pydantic.BaseModel):
    """Stock asset.

    迅投股票账号资金结构.

    Attributes:
        account_type: int, 资金账号类型
        account_id: str, 资金账号
        cash: float, 可用
        frozen_cash: float, 冻结
        market_value: float, 持仓市值
        total_asset: float 总资产
    """
    account_type: int
    account_id: str
    cash: float
    frozen_cash: float
    market_value: float
    total_asset: float
