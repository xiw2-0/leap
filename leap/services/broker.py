import asyncio
import logging
import time
import typing

from leap.config import settings
from leap.models import asset
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
