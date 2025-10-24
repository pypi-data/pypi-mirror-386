import datetime
from abc import ABC
from typing import Optional, List, cast, Dict, Set

from async_lru import alru_cache
from beanie import DecimalAnnotation, Link

from sirius import common
from sirius.common import PersistedDataClass
from sirius.market_data import Stock, StockMarketData, Option, MarketDataException
from sirius.market_data.alpha_vantage import AlphaVantageOption
from sirius.market_data.ibkr import IBKRStockMarketData, IBKRStock


class CachedStock(PersistedDataClass, Stock):  # type:ignore[misc]

    @staticmethod
    @alru_cache(maxsize=50, ttl=86_400)  # 24 hour cache
    async def _find_from_data_provider(ticker: str) -> Optional["CachedStock"]:
        ibkr_stock: IBKRStock = cast(IBKRStock, await IBKRStock._find(ticker))
        return CachedStock(
            id=ibkr_stock.ticker,
            name=ibkr_stock.name,
            ticker=ibkr_stock.ticker,
            currency=ibkr_stock.currency
        )

    @staticmethod
    @alru_cache(maxsize=50, ttl=86_400)  # 24 hour cache
    async def _find(ticker: str) -> Optional["Stock"]:
        cached_stock: CachedStock | None = await CachedStock.get(ticker)
        if cached_stock:
            return cached_stock

        return await CachedStock._update_cache(ticker)

    @staticmethod
    @alru_cache(maxsize=50, ttl=86_400)  # 24 hour cache
    async def _update_cache(ticker: str) -> Stock:
        stock = await CachedStock._find_from_data_provider(ticker)
        if not stock:
            raise MarketDataException(f"Could not find stock from data provider with ticker: {ticker}")

        return await stock.save()


class CachedStockMarketData(PersistedDataClass, StockMarketData):  # type:ignore[misc]
    open: DecimalAnnotation
    high: DecimalAnnotation
    low: DecimalAnnotation
    close: DecimalAnnotation
    stock: Link[CachedStock]  # type: ignore[assignment]

    @staticmethod
    @alru_cache(maxsize=50, ttl=43_200)  # 12 hour cache
    async def _get_from_data_provider(ticker: str, from_timestamp: datetime.datetime) -> List["CachedStockMarketData"]:
        abstract_stock: Stock = await Stock.get(ticker)
        stock: CachedStock = cast(CachedStock, await CachedStock._get_local_object(abstract_stock))
        latest_market_data_list: List[StockMarketData] = await IBKRStockMarketData._get(abstract_stock, from_timestamp, datetime.datetime.now())

        return [CachedStockMarketData(
            id=f"{market_data.stock.ticker} | {int(market_data.timestamp.timestamp())}",
            open=market_data.open,
            high=market_data.high,
            low=market_data.low,
            close=market_data.close,
            timestamp=market_data.timestamp,
            stock=stock)
            for market_data in latest_market_data_list]

    @staticmethod
    async def _update_cache(ticker: str, from_timestamp: datetime.datetime | None = None) -> List["CachedStockMarketData"]:
        from_timestamp = (datetime.datetime.now().replace(year=datetime.datetime.now().year - 10)) if not from_timestamp else from_timestamp  # 10 years
        current_data: Dict[str, CachedStockMarketData] = {data.id: data for data in await CachedStockMarketData._get_all(ticker, is_update_cache=False)}
        latest_data: Dict[str, CachedStockMarketData] = {data.id: data for data in await CachedStockMarketData._get_from_data_provider(ticker, from_timestamp)}
        new_data_ids: Set[str] = latest_data.keys() - current_data.keys()
        unique_data_to_update_list: List[CachedStockMarketData] = [latest_data[k] for k in new_data_ids]
        await CachedStockMarketData.insert_many(unique_data_to_update_list)

        return unique_data_to_update_list

    @staticmethod
    @alru_cache(maxsize=50, ttl=43_200)  # 12 hour cache
    async def _get_all(ticker: str, is_update_cache: bool = True) -> List["CachedStockMarketData"]:
        if not common.is_test_environment():
            all_data_list: List[CachedStockMarketData] = await CachedStockMarketData.find(CachedStockMarketData.stock.id == ticker, fetch_links=False).to_list()  # type: ignore[attr-defined]
        else:
            all_data_list = [c for c in await CachedStockMarketData.find_all().to_list() if c.stock.ref.id == ticker]

        latest_data: CachedStockMarketData | None = max(all_data_list, key=lambda d: d.timestamp) if all_data_list else None
        expected_latest_data_date: datetime.datetime = common.get_previous_business_day(datetime.datetime.now())

        if is_update_cache and (not all_data_list or (expected_latest_data_date - latest_data.timestamp).days > 1):
            all_data_list = all_data_list + await CachedStockMarketData._update_cache(ticker, latest_data.timestamp if latest_data else None)

        return all_data_list

    @staticmethod
    async def _get(abstract_stock: Stock, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> List["StockMarketData"]:
        from_timestamp = common.get_next_business_day_adjusted_date(from_timestamp)
        to_timestamp = common.get_previous_business_day_adjusted_date(to_timestamp)
        cached_data_list: List[CachedStockMarketData] = await CachedStockMarketData._get_all(abstract_stock.ticker)

        return [obj for obj in cached_data_list if from_timestamp <= obj.timestamp <= to_timestamp]


class CachedOption(PersistedDataClass, Option, ABC):
    strike_price: DecimalAnnotation
    underlying_stock: Link[CachedStock]  # type: ignore[assignment]

    async def get_underlying_stock(self) -> Stock:
        if isinstance(self.underlying_stock, Link):
            self.underlying_stock = await self.underlying_stock.fetch()

        return self.underlying_stock  # type: ignore[return-value]

    @staticmethod
    async def _update_cache(ticker: str, number_of_days_to_expiry: int) -> List["CachedOption"]:
        new_data_list: List[CachedOption] = await CachedOption._find_from_data_provider(ticker, number_of_days_to_expiry)
        await CachedOption.insert_many(new_data_list)
        return new_data_list

    @staticmethod
    @alru_cache(maxsize=50, ttl=86_400)  # 24 hour cache
    async def _find_from_data_provider(ticker: str, number_of_days_to_expiry: int) -> List["CachedOption"]:
        stock: Stock | None = await Stock.find(ticker)
        if not stock:
            return []

        cached_stock: CachedStock | None = await CachedStock.get(ticker)
        all_option_list: List[Option] = await AlphaVantageOption._find_all_options(ticker, number_of_days_to_expiry)
        return [CachedOption(
            id=f"{ticker} | {option.expiry_date.strftime("%Y-%m-%d")} | {common.get_decimal_str(option.strike_price)} | {option.type.upper()}",
            name=f"{ticker} | {option.expiry_date.strftime("%Y-%m-%d")} | {common.get_decimal_str(option.strike_price)} | {option.type.upper()}",
            strike_price=option.strike_price,
            expiry_date=option.expiry_date,
            type=option.type,
            currency=option.currency,
            underlying_stock=cached_stock
        ) for option in all_option_list]

    @staticmethod
    @alru_cache(maxsize=50, ttl=86_400)  # 24 hour cache
    async def _find_all_options(ticker: str, number_of_days_to_expiry: int, is_update_cache: bool = True) -> List["Option"]:
        expiry_date: datetime.date = datetime.datetime.now().date() + datetime.timedelta(days=number_of_days_to_expiry)
        options_list: List[CachedOption] = await CachedOption.find(CachedOption.underlying_stock.id == ticker).to_list()  # type: ignore[attr-defined]

        if len(options_list) == 0 and is_update_cache:
            options_list = options_list + await CachedOption._update_cache(ticker, number_of_days_to_expiry)

        return [option for option in options_list if option.expiry_date == expiry_date]
