import datetime
from decimal import Decimal
from typing import List

from sirius import common
from sirius.constants import EnvironmentSecretKey
from sirius.http_requests import AsyncHTTPSession, HTTPResponse
from sirius.market_data import Option, Stock

BASE_URL: str = "https://www.alphavantage.co/query"


class AlphaVantageOption(Option):

    @staticmethod
    async def __find_all_from_ticker(ticker: str) -> List["AlphaVantageOption"]:
        option_list: List[AlphaVantageOption] = []
        underlying_stock: Stock = await Stock.find(ticker)
        if not underlying_stock:
            return []

        response: HTTPResponse = await AsyncHTTPSession(BASE_URL).get(f"{BASE_URL}", query_params={
            "function": "HISTORICAL_OPTIONS",
            "symbol": underlying_stock.ticker,
            "apikey": await common.get_environmental_secret(EnvironmentSecretKey.ALPHA_VANTAGE_API_KEY)
        })

        for data in response.data["data"]:
            expiry_date: datetime.date = datetime.datetime.strptime(data["expiration"], "%Y-%m-%d").date()
            strike_price: Decimal = Decimal(data["strike"])
            type_str: str = str(data["type"]).upper()
            option_list.append(AlphaVantageOption(
                underlying_stock=underlying_stock,
                strike_price=strike_price,
                expiry_date=datetime.datetime.strptime(data["expiration"], "%Y-%m-%d").date(),
                type=type_str,
                currency=underlying_stock.currency,
                name=f"{ticker} | {expiry_date.strftime("%Y-%m-%d")} | {common.get_decimal_str(strike_price)} | {type_str}"
            ))

        return option_list

    @staticmethod
    async def _find_all_options(ticker: str, number_of_days_to_expiry: int) -> List["Option"]:
        return [option for option in await AlphaVantageOption.__find_all_from_ticker(ticker)
                if (option.expiry_date - datetime.datetime.now().date()).days <= number_of_days_to_expiry]
