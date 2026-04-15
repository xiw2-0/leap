from leap.models.quote import Tick

import httpx
import datetime


class TencentQuote(object):
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
        self.base_url = "http://qt.gtimg.cn/q="
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

    def to_tencent_code(self, securities: list[str]) -> list[str]:
        """From 000000.SZ to sz000000; from 600000.SH to sh600000; from 00001.HK to r_hk00001"""
        tencent_codes: list[str] = []
        for code in securities:
            if code.endswith('.SZ'):
                tencent_codes.append('sz' + code[:-3])
            elif code.endswith('.SH'):
                tencent_codes.append('sh' + code[:-3])
            elif code.endswith('.HK'):
                tencent_codes.append('r_hk' + code[:-3])
            else:
                raise ValueError(f"Unsupported stock code format: {code}")
        return tencent_codes

    def from_tencent_code(self, tencent_codes: list[str]) -> list[str]:
        """From sz000000 to 000000.SZ; from sh600000 to 600000.SH; from r_hk00001 to 00001.HK"""
        standard_codes: list[str] = []
        for code in tencent_codes:
            if code.startswith('sz'):
                standard_codes.append(code[2:] + '.SZ')
            elif code.startswith('sh'):
                standard_codes.append(code[2:] + '.SH')
            elif code.startswith('r_hk'):
                standard_codes.append(code[4:] + '.HK')
            else:
                raise ValueError(
                    f"Unsupported Tencent stock code format: {code}")
        return standard_codes

    async def get_tick(self, securities: list[str]) -> list[Tick]:
        """Returns realtime tick data from Tencent Finance.

        Args:
            securities: Stock code list (e.g. ['sh600519', 'sz002475'])

        Returns:
            List of stock tick data
        """
        # 构造请求 URL
        stock_codes = self.to_tencent_code(securities)
        request_url = self.base_url + ",".join(stock_codes)

        response = await self.client.get(request_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch data from Tencent API, error message: {response.text}")

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

        # 提取股票代码
        stock_code = stock_info[0].split("v_")[-1]
        stock_code = self.from_tencent_code([stock_code])[0]

        # 解析数据
        fields = stock_info[1].strip().split("~")
        if len(fields) < 49:
            return None

        # Parse the time string into a timestamp in milliseconds
        timestamp_ms = self._parse_date_time(fields[30], stock_code[-2:])

        # Prepare bid and ask prices/volumes
        bid_prices = [
            float(fields[9]),   # bid1_price
            float(fields[11]),  # bid2_price
            float(fields[13]),  # bid3_price
            float(fields[15]),  # bid4_price
            float(fields[17])   # bid5_price
        ]
        bid_volumes = [
            int(fields[10]),    # bid1_volume
            int(fields[12]),    # bid2_volume
            int(fields[14]),    # bid3_volume
            int(fields[16]),    # bid4_volume
            int(fields[18])     # bid5_volume
        ]
        ask_prices = [
            float(fields[19]),  # ask1_price
            float(fields[21]),  # ask2_price
            float(fields[23]),  # ask3_price
            float(fields[25]),  # ask4_price
            float(fields[27])   # ask5_price
        ]
        ask_volumes = [
            int(fields[20]),    # ask1_volume
            int(fields[22]),    # ask2_volume
            int(fields[24]),    # ask3_volume
            int(fields[26]),    # ask4_volume
            int(fields[28])     # ask5_volume
        ]

        tick = Tick(
            stock_code=stock_code,
            time=timestamp_ms,  # Actual timestamp in milliseconds
            last_price=float(fields[3]),  # Current price
            open=float(fields[5]),  # Today's opening price
            high=float(fields[33]),  # Highest price today
            low=float(fields[34]),  # Lowest price today
            last_close=float(fields[4]),  # Yesterday's closing price
            amount=float(fields[37]) * 10000,  # Turnover (in yuan)
            volume=int(float(fields[6])),  # Volume (in hands)
            # Using volume as pvolume since Tencent doesn't provide this separately
            pvolume=int(float(fields[6])),
            stock_status=0,  # Placeholder - Tencent doesn't provide stock status directly
            open_int=0,  # Placeholder - Tencent doesn't provide open interest
            # Placeholder - Tencent doesn't provide last settlement price
            last_settlement_price=0.0,
            ask_prices=ask_prices,
            bid_prices=bid_prices,
            ask_vols=ask_volumes,
            bid_vols=bid_volumes
        )
        return tick

    def _parse_date_time(self, dt_str: str, market: str) -> int:
        if market == 'HK':
            splits = dt_str.split(' ')
            date_part = splits[0].replace('/', '')
            time_part = splits[1].replace(':', '')
        else:
            date_part = dt_str[:8]
            time_part = dt_str[-6:]

        # Format the datetime string to parse it
        formatted_datetime = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
        dt = datetime.datetime.strptime(
            formatted_datetime, "%Y-%m-%d %H:%M:%S")
        return int(dt.timestamp() * 1000)  # Convert to milliseconds and return

    async def close(self):
        """Close the httpx client"""
        await self.client.aclose()


if __name__ == "__main__":
    import asyncio

    async def main():
        api = TencentQuote()

        stock_codes = ["600519.SH", "002475.SZ",
                       "159937.SZ", '688126.SH',
                       "01810.HK"]  # 股票代码列表
        stock_data = await api.get_tick(stock_codes)
        print(f'Ticks:\n{stock_data}')
        await api.close()

    asyncio.run(main())
