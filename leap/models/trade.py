import pydantic


class OrderStockRequest(pydantic.BaseModel):
    """Request to make an order."""

    stock_code: str = pydantic.Field(..., description="证券代码, 例如\"600000.SH\"")
    order_type: int = pydantic.Field(..., description="委托类型, 23:买, 24:卖")
    order_volume: int = pydantic.Field(...,
                                       description="委托数量, 股票以'股'为单位, 债券以'张'为单位")
    price_type: int = pydantic.Field(..., description="""
    报价类型 - 
        xtconstant.LATEST_PRICE 5 最新价，但仍然是限价单
        xtconstant.FIX_PRICE 11 指定价
            上交所 股票
        xtconstant.MARKET_SH_CONVERT_5_CANCEL 42 最优五档即时成交剩余撤销
        xtconstant.MARKET_SH_CONVERT_5_LIMIT 43 最优五档即时成交剩转限价
        xtconstant.MARKET_PEER_PRICE_FIRST 44 对手方最优价格委托
        xtconstant.MARKET_MINE_PRICE_FIRST 45 本方最优价格委托
            深交所 股票 期权
        xtconstant.MARKET_PEER_PRICE_FIRST 44  对手方最优价格委托
        xtconstant.MARKET_MINE_PRICE_FIRST 45 本方最优价格委托
        xtconstant.MARKET_SZ_INSTBUSI_RESTCANCEL 46 即时成交剩余撤销委托
        xtconstant.MARKET_SZ_CONVERT_5_CANCEL 47 最优五档即时成交剩余撤销
        xtconstant.MARKET_SZ_FULL_OR_CANCEL 48 全额成交或撤销委托
    """)
    price: float = pydantic.Field(..., description="""
    报价价格 - 
        如果price_type为深市市价单/LATEST_PRICE, 那price填0, 其他需要指定价格 (或保护价格)
    """)
    strategy_name: str = pydantic.Field(..., description="策略名称")
    order_remark: str = pydantic.Field(..., description="委托备注")
