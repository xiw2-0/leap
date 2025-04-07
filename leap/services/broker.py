import asyncio
import logging
import time
import typing

from leap.config import settings
from leap.models import asset, trade
from leap.services import publisher
from leap.utils import singleton, model_util

from xtquant import xttrader, xttype  # type: ignore


@singleton.singleton
class XtBroker(object):
    def __init__(self) -> None:
        qmt_data_path = settings.QMT_DATA_PATH
        self._xt_trader = self._setup_xt_trader(path=qmt_data_path)

        xt_publisher = publisher.XtPublisher()
        self._xt_trader.register_callback(  # type: ignore
            callback=xt_publisher)

        qmt_account = settings.QMT_ACCOUNT
        self._xt_account = self._setup_xt_account(qmt_account, self._xt_trader)
        sub = self._xt_trader.subscribe(self._xt_account)  # type: ignore
        assert sub == 0, f'Subscribe to account {self._xt_account} failed'

    def _setup_xt_trader(self, path: str) -> xttrader.XtQuantTrader:
        """Sets up XtQuantTrader and returns it."""
        # 生成session id 整数类型 同时运行的策略不能重复
        session_id = int(time.time() % 100)
        # 指定客户端所在路径, 券商端指定到 userdata_mini文件夹
        trader = xttrader.XtQuantTrader(path, session_id)

        # 启动交易线程
        trader.start()
        # 建立交易连接，返回0表示连接成功
        connect_result = trader.connect()  # type: ignore
        assert connect_result == 0, '建立交易连接失败'
        logging.info(f'Connected to QMT successfully, path: {path}')

        return trader

    def _setup_xt_account(self, account: str, xt_trader: xttrader.XtQuantTrader) -> xttype.StockAccount:
        """Sets up Xt StockAccount and returns it."""
        # 创建资金账号为 account 的证券账号对象
        # 股票账号为STOCK 信用CREDIT 期货FUTURE
        xt_account: xttype.StockAccount = xttype.StockAccount(
            account, 'STOCK')  # type: ignore

        # 取账号信息
        account_info: xttype.XtAsset = xt_trader.query_stock_asset(  # type: ignore
            xt_account)
        assert account_info.total_asset > 0, f'股票账户 {account} 总资产为空'

        # 取可用资金
        available_cash = account_info.cash
        logging.info(f'股票账户 {account} 可用资金 {available_cash}')

        return xt_account

    async def query_stock_asset_async(self) -> asset.XtAsset:
        """异步查询股票资产信息"""
        future: asyncio.Future[asset.XtAsset] = asyncio.Future()

        def callback(result: typing.Any) -> None:
            nonlocal future
            future.set_result(result)

        self._xt_trader.query_stock_asset_async(  # type: ignore
            self._xt_account, callback)

        # 等待 Future 完成，并获取结果
        asset_ = await future

        return model_util.to_pydantic_model(asset_, asset.XtAsset)

    async def order_stock_async(self, order_request: trade.OrderStockRequest) -> int:
        """返回下单请求序号, 成功委托后的下单请求序号为大于0的正整数, 如果为-1表示委托失败"""
        return self._xt_trader.order_stock_async(  # type: ignore
            account=self._xt_account,
            stock_code=order_request.stock_code,
            order_type=order_request.order_type,
            order_volume=order_request.order_volume,
            price_type=order_request.price_type,
            price=order_request.price,
            strategy_name=order_request.strategy_name,
            order_remark=order_request.order_remark)

    async def cancel_order_stock_async(self, order_id: int) -> int:
        """返回撤单请求序号, 成功委托后的撤单请求序号为大于0的正整数, 如果为-1表示撤单失败"""
        return self._xt_trader.cancel_order_stock_async(  # type: ignore
            self._xt_account, order_id)

    async def query_stock_positions_async(self) -> list[asset.XtPosition]:
        future: asyncio.Future[list[asset.XtPosition]] = asyncio.Future()

        def callback(result: typing.Any) -> None:
            nonlocal future
            future.set_result(result)

        self._xt_trader.query_stock_positions_async(  # type: ignore
            self._xt_account, callback)
        positions = await future
        positions = [model_util.to_pydantic_model(position, asset.XtPosition)
                     for position in positions]
        return positions

    def query_stock_position(self, stock_code: str) -> asset.XtPosition:
        position: xttype.XtPosition = self._xt_trader.query_stock_position(  # type: ignore
            self._xt_account, stock_code)
        return model_util.to_pydantic_model(position, asset.XtPosition)

    async def query_stock_orders_async(self) -> list[trade.XtOrder]:
        future: asyncio.Future[list[trade.XtOrder]] = asyncio.Future()

        def callback(result: typing.Any) -> None:
            nonlocal future
            future.set_result(result)

        self._xt_trader.query_stock_orders_async(  # type: ignore
            self._xt_account, callback, cancelable_only=False)
        orders = await future
        return [model_util.to_pydantic_model(order, trade.XtOrder) for order in orders]

    async def query_stock_trades_async(self) -> list[trade.XtTrade]:
        future: asyncio.Future[list[trade.XtTrade]] = asyncio.Future()

        def callback(result: typing.Any) -> None:
            nonlocal future
            future.set_result(result)

        self._xt_trader.query_stock_trades_async(  # type: ignore
            self._xt_account, callback)
        trades = await future
        return [model_util.to_pydantic_model(t, trade.XtTrade) for t in trades]
