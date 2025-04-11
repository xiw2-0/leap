import pydantic


class Tick(pydantic.BaseModel):
    """Tick."""

    stock_code: str = pydantic.Field(..., description="股票代码")
    time: str = pydantic.Field(..., description="时间戳")
    last_price: float = pydantic.Field(..., description="最新价")
    open: float = pydantic.Field(..., description="开盘价")
    high: float = pydantic.Field(..., description="最高价")
    low: float = pydantic.Field(..., description="最低价")
    last_close: float = pydantic.Field(..., description="前收盘价")
    amount: float = pydantic.Field(..., description="成交总额")
    volume: float = pydantic.Field(..., description="成交总量")
    pvolume: float = pydantic.Field(..., description="原始成交总量")
    stock_status: int = pydantic.Field(..., description="证券状态")
    open_int: int = pydantic.Field(..., description="持仓量")
    last_settlement_price: float = pydantic.Field(..., description="前结算价")
    ask_prices: list[float] = pydantic.Field(..., description="委卖价")
    bid_prices: list[float] = pydantic.Field(..., description="委买价")
    ask_vols: list[int] = pydantic.Field(..., description="委卖量")
    bid_vols: list[int] = pydantic.Field(..., description="委买量")
