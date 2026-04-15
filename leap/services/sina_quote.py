from leap.models.quote import Tick
from leap.utils import singleton

import httpx
import asyncio
import datetime

@singleton.singleton
class SinaQuote(object):
    def __init__(self):
        # Initialize httpx async client with longer keep-alive timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=30.0,
                write=30.0,
                pool=5.0
            ),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=120.0  # Keep-alive timeout in seconds
            )
        )
        # Store base URL and headers as constants
        self.base_url = "http://hq.sinajs.cn/list="
        self.headers = {
            "Referer": "http://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

    def to_sina_code(self, securities: list[str]) -> list[str]:
        """From 000000.SZ to sz000000; from 600000.SH to sh600000; from 00001.HK to rt_hk00001"""
        sina_codes: list[str] = []
        for code in securities:
            if code.endswith('.SZ'):
                sina_codes.append('sz' + code[:-3])
            elif code.endswith('.SH'):
                sina_codes.append('sh' + code[:-3])
            elif code.endswith('.HK'):
                sina_codes.append('rt_hk' + code[:-3])
            else:
                raise ValueError(f"Unsupported stock code format: {code}")
        return sina_codes

    def from_sina_code(self, sina_codes: list[str]) -> list[str]:
        """From sz000000 to 000000.SZ; from sh600000 to 600000.SH; from rt_hk00001 to 00001.HK"""
        standard_codes: list[str] = []
        for code in sina_codes:
            if code.startswith('sz'):
                standard_codes.append(code[2:] + '.SZ')
            elif code.startswith('sh'):
                standard_codes.append(code[2:] + '.SH')
            elif code.startswith('rt_hk'):
                standard_codes.append(code[5:] + '.HK')
            else:
                raise ValueError(f"Unsupported Sina stock code format: {code}")
        return standard_codes

    async def get_tick(self, securities: list[str]) -> list[Tick]:
        """Returns realtime tick data from Sina Finance.

        Args:
            securities: Stock code list (e.g. ['600519.SH', '002475.SZ'])

        Returns:
            List of stock tick data
        """
        # 构造请求 URL
        sina_codes = self.to_sina_code(securities)
        request_url = self.base_url + ",".join(sina_codes)

        response = await self.client.get(request_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch data from Sina API, error message: {response.text}")

        # 解析响应数据
        result: list[Tick] = []
        for data in response.text.split(";"):
            if not data:
                continue
            tick = self._parse_tick(data)
            if not tick:
                continue
            result.append(tick)
        return result

    def _parse_tick(self, data: str):
        stock_info = data.split("=")
        if len(stock_info) < 2:
            return None
        stock_code = stock_info[0].split("hq_str_")[-1]
        # Check if stock_code is valid
        if not stock_code or stock_code.strip() == "":
            return None

        stock_code = self.from_sina_code([stock_code])[0]

        stock_data = stock_info[1].strip()[1:-1]  # 去掉两端的引号
        stock_data = stock_data.split(",")

        # Check if we have data before trying to parse it
        if len(stock_data) <= 1 or (len(stock_data) == 1 and stock_data[0] == ""):
            return None

        if stock_code[-2:] == "HK":
            return self._parse_hk_tick(stock_code, stock_data)
        return self._parse_a_share_tick(stock_code, stock_data)

    def _parse_a_share_tick(self, stock_code: str, stock_data: list[str]):
        # Check if we have enough data for A-share parsing
        if len(stock_data) < 32:
            return None

        # Parse the time string into a timestamp
        date_part = stock_data[30]  # Date in format YYYY-MM-DD
        time_part = stock_data[31]  # Time in format HH:MM:SS
        # Combine date and time and convert to Unix timestamp in milliseconds
        datetime_str = f"{date_part} {time_part}"
        dt = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        timestamp_ms = int(dt.timestamp() * 1000)  # Convert to milliseconds

        # Extract bid and ask prices/volumes for both sides
        bid_prices = [
            float(stock_data[11]),
            float(stock_data[13]),
            float(stock_data[15]),
            float(stock_data[17]),
            float(stock_data[19])
        ]
        bid_volumes = [
            int(stock_data[10]),
            int(stock_data[12]),
            int(stock_data[14]),
            int(stock_data[16]),
            int(stock_data[18])
        ]
        ask_prices = [
            float(stock_data[21]),
            float(stock_data[23]),
            float(stock_data[25]),
            float(stock_data[27]),
            float(stock_data[29])
        ]
        ask_volumes = [
            int(stock_data[20]),
            int(stock_data[22]),
            int(stock_data[24]),
            int(stock_data[26]),
            int(stock_data[28])
        ]

        tick = Tick(
            stock_code=stock_code,
            time=timestamp_ms,  # Actual timestamp in milliseconds
            last_price=float(stock_data[3]),
            open=float(stock_data[1]),
            high=float(stock_data[4]),
            low=float(stock_data[5]),
            last_close=float(stock_data[2]),
            amount=float(stock_data[9]),
            volume=int(stock_data[8]),
            # Using volume as pvolume since Sina doesn't provide this
            pvolume=int(stock_data[8]),
            stock_status=0,  # Placeholder - Sina doesn't provide stock status directly
            open_int=0,  # Placeholder - Sina doesn't provide open interest
            last_settlement_price=0.0,  # Placeholder - Sina doesn't provide last settlement price
            ask_prices=ask_prices,
            bid_prices=bid_prices,
            ask_vols=ask_volumes,
            bid_vols=bid_volumes
        )
        return tick

    def _parse_hk_tick(self, stock_code: str, stock_data: list[str]):
        # Check if we have enough data for HK parsing
        if len(stock_data) < 19:
            return None

        # Parse the time string into a timestamp for HK stocks
        date_part = stock_data[17]  # Date in format YYYY/MM/DD for HK
        time_part = stock_data[18]  # Time in format HH:MM:SS for HK
        # Combine date and time and convert to Unix timestamp in milliseconds
        datetime_str = f"{date_part} {time_part}"
        dt = datetime.datetime.strptime(datetime_str, "%Y/%m/%d %H:%M:%S")
        timestamp_ms = int(dt.timestamp() * 1000)  # Convert to milliseconds

        tick = Tick(
            stock_code=stock_code,
            time=timestamp_ms,  # Actual timestamp in milliseconds
            last_price=float(stock_data[4]),
            open=float(stock_data[2]),
            high=float(stock_data[6]),
            low=float(stock_data[5]),
            last_close=float(stock_data[3]),
            amount=float(stock_data[11]),
            volume=int(stock_data[12]),
            # Using volume as pvolume since Sina doesn't provide this
            pvolume=int(stock_data[12]),
            stock_status=0,  # Placeholder - Sina doesn't provide stock status directly
            open_int=0,  # Placeholder - Not applicable for HK stocks
            last_settlement_price=0.0,  # Placeholder - Sina doesn't provide last settlement price
            ask_prices=[float(stock_data[10])],  # Simple ask price for HK
            bid_prices=[float(stock_data[9])],  # Simple bid price for HK
            # Placeholder - Sina doesn't provide detailed volumes for HK
            ask_vols=[0],
            # Placeholder - Sina doesn't provide detailed volumes for HK
            bid_vols=[0]
        )
        return tick

    async def close(self):
        """Close the httpx client"""
        await self.client.aclose()


if __name__ == "__main__":
    import asyncio

    async def main():
        api = SinaQuote()

        stock_codes = ['600092.SH', '600181.SH', '600003.SH', '600263.SH', '600001.SH', '600253.SH', '600205.SH', '600357.SH', '600065.SH', '600002.SH']  # 股票代码列表
        stock_data = await api.get_tick(stock_codes)
        print(f'Ticks:\n{stock_data}')

        await api.close()

    asyncio.run(main())
