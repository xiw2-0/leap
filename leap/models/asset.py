import pydantic


class XtAsset(pydantic.BaseModel):
    """Stock asset. 迅投股票账号资金结构."""

    account_type: int = pydantic.Field(..., description="资金账号类型")
    account_id: str = pydantic.Field(..., description="资金账号")
    cash: float = pydantic.Field(..., description="可用现金")
    frozen_cash: float = pydantic.Field(..., description="冻结现金")
    market_value: float = pydantic.Field(..., description="持仓市值")
    total_asset: float = pydantic.Field(..., description="总资产")
