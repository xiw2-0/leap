import asyncio
import datetime
import logging


from leap.services import tencent_quote
from leap.services.trading_calendar import TradingCalendar
from leap.services.quote_push_service import QuotePushService


class QuoteGuard:
    """
    A guard service to monitor quote push service and trigger backup mechanism
    when primary quote source becomes unstable.

    The guard runs continuously during trading days, checking if the latest tick time
    is stale compared to current time. If it is, it fetches fresh data from Tencent
    and pushes it using the backup mechanism.
    """

    def __init__(self, work_sleep: float, latency_threshold: float,
                 tencent_quote: tencent_quote.TencentQuote, quote_push_service: QuotePushService, trading_calendar: TradingCalendar):
        """
        Initialize the quote guard.

        Args:
            work_sleep: Time to sleep between checks during working hours
            latency_threshold: Threshold in seconds beyond which data is considered stale
            tencent_quote: Optional TencentQuote instance for testing
            quote_push_service: Optional QuotePushService instance for testing
            trading_calendar: Optional TradingCalendar instance for testing
        """
        self.work_sleep = work_sleep
        self.latency_threshold = latency_threshold
        self._stopped = False
        self._logger = logging.getLogger(__name__)

        # Working time: 9:00 ~ 15:30
        self._work_start = datetime.time(9, 0)
        self._work_end = datetime.time(15, 30)

        # Guard time: 9:30~11:30 and 13:00~15:00
        self._morning_start = datetime.time(9, 30)
        self._morning_end = datetime.time(11, 30)
        self._afternoon_start = datetime.time(13, 0)
        self._afternoon_end = datetime.time(15, 0)

        self._trading_calendar = trading_calendar
        self._tencent_quote = tencent_quote
        self._quote_push_service = quote_push_service

    def is_guard_time(self, current_time: datetime.time) -> bool:
        """
        Check if the current time is within guard time (9:30~11:30 and 13:00~15:00).

        Args:
            current_time: Current time to check

        Returns:
            True if within guard time, False otherwise
        """
        morning_session = self._morning_start <= current_time <= self._morning_end
        afternoon_session = self._afternoon_start <= current_time <= self._afternoon_end
        return morning_session or afternoon_session

    def is_working_time(self, current_time: datetime.time) -> bool:
        """
        Check if the current time is within working time (9:00~15:30).

        Args:
            current_time: Current time to check

        Returns:
            True if within working time, False otherwise
        """
        return self._work_start <= current_time <= self._work_end

    async def run(self):
        """
        Main run loop for the quote guard.
        """
        self._logger.info("Starting quote guard...")

        while not self._stopped:
            # Check if today is a trading day
            if self._trading_calendar.is_today_trading():
                # Only run during working hours - stay in this loop while in working hours
                current_time = datetime.datetime.now().time()
                while not self._stopped and self.is_working_time(current_time):
                    # Only perform guard checks during guard time
                    if self.is_guard_time(current_time):
                        await self.guard()

                    # Sleep between checks during working hours
                    await asyncio.sleep(self.work_sleep)
                    current_time = datetime.datetime.now().time()

            # Outside working hours, sleep longer
            await asyncio.sleep(600)  # Sleep for 10 minutes
        self._logger.info("Quote guard stopped.")

    async def guard(self):
        """
        Perform the guard check to see if backup data is needed.
        """

        # Get the max tick time from the quote push service
        # max_tick_time is already in milliseconds
        max_tick_time = self._quote_push_service.get_max_tick_time()

        current_time_ms = datetime.datetime.now().timestamp() * 1000

        # Calculate the threshold in milliseconds (3 seconds + latency threshold)
        threshold_ms = (3 + self.latency_threshold) * 1000

        # Check if the max tick time is too old
        if current_time_ms <= max_tick_time + threshold_ms:
            return

        self._logger.warning(
            f"Quote data is stale. Max tick time: {max_tick_time}, "
            f"Current time: {current_time_ms}, Threshold: {threshold_ms}ms"
        )

        # Get all subscribed stocks from the push service
        subscribed_stocks = self._quote_push_service.get_subscribed_stocks()

        if not subscribed_stocks:
            self._logger.info("No subscribed stocks to check.")
            return

        # Get fresh quotes from Tencent
        try:
            ticks = await self._tencent_quote.get_tick(subscribed_stocks)

            for tick in ticks:
                await self._quote_push_service.push_quote_update_from_backup(
                    datetime.datetime.now(),
                    tick
                )

        except Exception as e:
            self._logger.error(f"Error fetching backup quotes: {e}")

    def stop(self):
        """
        Stop the quote guard.
        """
        self._logger.info("Stopping quote guard...")
        self._stopped = True
