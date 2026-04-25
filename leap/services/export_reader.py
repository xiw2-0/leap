import pandas as pd
import typing

from leap.config import settings
from leap.models import trade
from leap.utils import model_util
from xtquant import xtconstant  # type: ignore

# Define column name mappings
_IPO_SUBSCRIPTION_NUMBER_MAPPING = {
    '成功': 'success',
    '返回信息': 'message',
    '资金账号': 'account_id',
    '市场': 'market',
    '交易市场类别': 'market_type',
    '股票代码': 'stock_code',
    '股票名称': 'stock_name',
    '起始配号': 'starting_allotment_number',
    '配号数量': 'allotment_count',
    '股东账号': 'holder_id',
    '配号日期': 'allotment_date',
    '申购日期': 'subscription_date'
}

_IPO_SUBSCRIPTION_RESULT_MAPPING = {
    '成功': 'success',
    '返回信息': 'message',
    '交易市场类别': 'market_type',
    '股东代码': 'holder_id',
    '股票代码': 'stock_code',
    '中签数量': 'lottery_shares',
    '中签价格': 'lottery_price',
    '中签金额': 'lottery_amount',
    '放弃数量': 'giveup_shares',
    '中签编号': 'lottery_number',
    '股票名称': 'stock_name',
    '中签日期': 'lottery_date',
    '申购日期': 'subscription_date',
    '资金账号': 'account_id'
}


class ExportReader(object):
    """The reader for exported data from XT Mini-QMT."""

    def __init__(self) -> None:
        self._path = settings.QMT_EXPORT_PATH
        self._account = settings.QMT_ACCOUNT

        reverse_type_dict = {v: k for k,
                             v in xtconstant.ACCOUNT_TYPE_DICT.items()}
        self._account_type = reverse_type_dict[settings.QMT_ACCOUNT_TYPE]

    def read_ipo_lucky_info(self) -> list[trade.IPOSubscriptionResult]:
        df = pd.read_csv(  # type: ignore
            f'{self._path}/{self._account}_{self._account_type}_IPOLuckyInfo.csv', encoding='gbk'
        )
        # Rename columns
        df = df.rename(columns=_IPO_SUBSCRIPTION_RESULT_MAPPING)
        records: list[dict[str, typing.Any]] = df.to_dict(  # type: ignore
            orient='records')
        print(df)

        return [model_util.pydantic_model_from_dict(record, trade.IPOSubscriptionResult) for record in records]

    def read_subscrib_number(self) -> list[trade.IPOSubscriptionNumber]:
        df = pd.read_csv(  # type: ignore
            f'{self._path}/{self._account}_{self._account_type}_subscribNumber.csv', encoding='gbk'
        )
        # Rename columns
        df = df.rename(columns=_IPO_SUBSCRIPTION_NUMBER_MAPPING)
        print(df)

        records: list[dict[str, typing.Any]] = df.to_dict(  # type: ignore
            orient='records')
        return [model_util.pydantic_model_from_dict(record, trade.IPOSubscriptionNumber) for record in records]
