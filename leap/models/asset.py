import pydantic


class XtAsset(pydantic.BaseModel):
    """Stock asset. 迅投股票账号资金结构."""

    account_type: int = pydantic.Field(..., description="资金账号类型")
    account_id: str = pydantic.Field(..., description="资金账号")
    cash: float = pydantic.Field(..., description="可用现金")
    frozen_cash: float = pydantic.Field(..., description="冻结现金")
    market_value: float = pydantic.Field(..., description="持仓市值")
    total_asset: float = pydantic.Field(..., description="总资产")


class XtPosition(pydantic.BaseModel):
    """Position. XT持仓结构."""

    account_type: int = pydantic.Field(..., description="资金账号类型")
    account_id: str = pydantic.Field(..., description="资金账号")
    stock_code: str = pydantic.Field(..., description="证券代码, 例如\"600000.SH\"")
    volume: int = pydantic.Field(..., description="持仓数量, 股票以'股'为单位, 债券以'张'为单位")
    can_use_volume: int = pydantic.Field(...,
                                         description="可用数量, 股票以'股'为单位, 债券以'张'为单位")
    open_price: float = pydantic.Field(..., description="开仓价")
    market_value: float = pydantic.Field(..., description="市值")
    frozen_volume: int = pydantic.Field(..., description="冻结数量")
    on_road_volume: int = pydantic.Field(..., description="在途股份")
    yesterday_volume: int = pydantic.Field(..., description="昨夜拥股")
    avg_price: float = pydantic.Field(..., description="成本价")
    direction: int = pydantic.Field(..., description="多空, 股票不需要")
    stock_code1: str = pydantic.Field(..., description="股票长代码")
