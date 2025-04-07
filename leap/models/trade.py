import pydantic


class XtOrder(pydantic.BaseModel):
    """Stock order. 迅投股票委托结构."""

    account_type: int = pydantic.Field(..., description="资金账号类型")
    account_id: str = pydantic.Field(..., description="资金账号")
    stock_code: str = pydantic.Field(..., description="证券代码, 例如\"600000.SH\"")
    order_id: int = pydantic.Field(..., description="委托编号")
    order_sysid: str = pydantic.Field(..., description="柜台编号")
    order_time: int = pydantic.Field(..., description="报单时间, Unix timestamp")
    order_type: int = pydantic.Field(..., description="委托类型, 23:买, 24:卖")
    order_volume: int = pydantic.Field(...,
                                       description="委托数量, 股票以'股'为单位, 债券以'张'为单位")
    price_type: int = pydantic.Field(..., description="""
    报价类型 - 
        xtconstant.LATEST_PRICE 5 最新价，但仍然是限价单
        xtconstant.FIX_PRICE 11 指定价
            上交所 股票
        xtconstant.MARKET_SH_CONVERT_5_CANCEL 42 最优五档即时成交剩余撤销
        xtconstant.MARKET_SH_CONVERT_5_LIMIT 43 最优五档即时成交
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
    traded_volume: int = pydantic.Field(..., description="""
    成交数量 - 
        股票以'股'为单位, 债券以'张'为单位
    """)
    traded_price: float = pydantic.Field(..., description="成交均价")
    order_status: int = pydantic.Field(..., description="委托状态")
    status_msg: str = pydantic.Field(..., description="委托状态描述, 如废单原因")
    strategy_name: str = pydantic.Field(..., description="策略名称")
    order_remark: str = pydantic.Field(..., description="委托备注")
    direction: int = pydantic.Field(..., description="多空, 股票不需要")
    offset_flag: int = pydantic.Field(..., description="""
    交易操作，用此字段区分股票买卖，期货开、平仓，期权买卖等
    """)
    stock_code1: str = pydantic.Field(..., description="股票长代码")


class XtTrade(pydantic.BaseModel):
    """Trading record. XT交易记录结构."""

    account_type: int = pydantic.Field(..., description="资金账号类型")
    account_id: str = pydantic.Field(..., description="资金账号")
    order_type: int = pydantic.Field(..., description="委托类型")
    stock_code: str = pydantic.Field(..., description="证券代码, 例如\"600000.SH\"")
    traded_id: str = pydantic.Field(..., description="成交编号")
    traded_time: int = pydantic.Field(..., description="成交时间, Unix timestamp")
    traded_price: float = pydantic.Field(..., description="成交均价")
    traded_volume: int = pydantic.Field(..., description="""
    成交数量 - 
        股票以'股'为单位, 债券以'张'为单位
    """)
    traded_amount: float = pydantic.Field(..., description="成交金额")
    order_id: int = pydantic.Field(..., description="委托编号")
    order_sysid: str = pydantic.Field(..., description="柜台编号")
    strategy_name: str = pydantic.Field(..., description="策略名称")
    order_remark: str = pydantic.Field(..., description="委托备注")
    direction: int = pydantic.Field(..., description="多空, 股票不需要")
    offset_flag: int = pydantic.Field(..., description="""
    交易操作，用此字段区分股票买卖，期货开、平仓，期权买卖等
    """)
    stock_code1: str = pydantic.Field(..., description="股票长代码")
    commission: float = pydantic.Field(..., description="手续费")


class XtOrderError(pydantic.BaseModel):
    """Order error. 迅投股票委托失败结构"""

    account_type: int = pydantic.Field(..., description="资金账号类型")
    account_id: str = pydantic.Field(..., description="资金账号")
    order_id: int = pydantic.Field(..., description="订单编号")
    error_id: int = pydantic.Field(..., description="报单失败错误码")
    error_msg: str = pydantic.Field(..., description="报单失败具体信息")
    strategy_name: str = pydantic.Field(..., description="策略名称")
    order_remark: str = pydantic.Field(..., description="委托备注")


class XtCancelError(pydantic.BaseModel):
    """Cancel error. 迅投股票委托撤单失败结构"""

    account_type: int = pydantic.Field(..., description="资金账号类型")
    account_id: str = pydantic.Field(..., description="资金账号")
    order_id: int = pydantic.Field(..., description="订单编号")
    market: int = pydantic.Field(..., description="""
    交易市场 0:上海 1:深圳
    """)
    order_sysid: str = pydantic.Field(..., description="柜台委托编号")
    error_id: int = pydantic.Field(..., description="撤单失败错误码")
    error_msg: str = pydantic.Field(..., description="撤单失败具体信息")


class XtOrderResponse(pydantic.BaseModel):
    """Order response. 迅投异步下单接口对应的委托反馈"""

    account_type: int = pydantic.Field(..., description="资金账号类型")
    account_id: str = pydantic.Field(..., description="资金账号")
    order_id: int = pydantic.Field(..., description="订单编号")
    strategy_name: str = pydantic.Field(..., description="策略名称")
    order_remark: str = pydantic.Field(..., description="委托备注")
    error_msg: str = pydantic.Field(..., description="下单反馈信息")
    seq: int = pydantic.Field(..., description="下单请求序号")


class XtCancelOrderResponse(pydantic.BaseModel):
    """Cancel order response. 迅投异步委托撤单请求返回结构"""

    account_type: int = pydantic.Field(..., description="资金账号类型")
    account_id: str = pydantic.Field(..., description="资金账号")
    cancel_result: int = pydantic.Field(..., description="撤单结果")
    order_id: int = pydantic.Field(..., description="订单编号")
    order_sysid: str = pydantic.Field(..., description="柜台委托编号")
    seq: int = pydantic.Field(..., description="撤单请求序号")
    error_msg: str = pydantic.Field(..., description="撤单反馈信息")


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
