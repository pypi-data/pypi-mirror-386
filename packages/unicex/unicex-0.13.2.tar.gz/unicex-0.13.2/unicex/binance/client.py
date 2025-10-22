__all__ = ["Client"]

import json
import time
import warnings
from typing import Any

from unicex._base import BaseClient
from unicex.exceptions import NotAuthorized
from unicex.types import RequestMethod
from unicex.utils import dict_to_query_string, filter_params, generate_hmac_sha256_signature


class Client(BaseClient):
    """Клиент для работы с Binance API."""

    _BASE_SPOT_URL: str = "https://api.binance.com"
    """Базовый URL для REST API Binance Spot."""

    _BASE_FUTURES_URL: str = "https://fapi.binance.com"
    """Базовый URL для REST API Binance Futures."""

    _RECV_WINDOW: int = 5000
    """Стандартный интервал времени для получения ответа от сервера."""

    def _get_headers(self) -> dict:
        """Возвращает заголовки для запросов к Binance API."""
        headers = {"Accept": "application/json"}
        if self._api_key:  # type: ignore[attr-defined]
            headers["X-MBX-APIKEY"] = self._api_key  # type: ignore[attr-defined]
        return headers

    def _prepare_payload(
        self,
        *,
        signed: bool,
        params: dict[str, Any] | None,
        data: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Подготавливает payload и заголовки для запроса.

        Если signed=True:
            - добавляет подпись и все обязательные параметры в заголовки

        Если signed=False:
            - возвращает только отфильтрованные params/data.

        Параметры:
            signed (`bool`): Нужно ли подписывать запрос.
            params (`dict | None`): Параметры для query string.
            data (`dict | None`): Параметры для тела запроса.

        Возвращает:
            tuple:
                - payload (`dict`): Параметры/тело запроса с подписью (если нужно).
                - headers (`dict | None`): Заголовки для запроса или None.
        """
        # Фильтруем параметры от None значений
        params = filter_params(params) if params else {}
        data = filter_params(data) if data else {}

        if not signed:
            return {"params": params, "data": data}, None

        if not self.is_authorized():
            raise NotAuthorized("Api key and api secret is required to private endpoints")

        # Объединяем все параметры в payload
        payload = {**params, **data}
        payload["timestamp"] = int(time.time() * 1000)
        payload["recvWindow"] = self._RECV_WINDOW

        # Генерируем подпись
        query_string = dict_to_query_string(payload)
        payload["signature"] = generate_hmac_sha256_signature(
            self._api_secret,  # type: ignore[attr-defined]
            query_string,
            "hex",
        )

        headers = self._get_headers()
        return payload, headers

    async def _make_request(
        self,
        method: RequestMethod,
        url: str,
        signed: bool = False,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Выполняет HTTP-запрос к эндпоинтам Binance API.

        Если signed=True, формируется подпись для приватных endpoint'ов:
            - Если переданы params — подпись добавляется в параметры запроса.
            - Если передан data — подпись добавляется в тело запроса.

        Если signed=False, запрос отправляется как публичный.

        Параметры:
            method (`str`): HTTP метод ("GET", "POST", "DELETE" и т.д.).
            url (`str`): Полный URL эндпоинта Binance API.
            signed (`bool`): Нужно ли подписывать запрос.
            params (`dict | None`): Query-параметры.
            data (`dict | None`): Тело запроса.

        Возвращает:
            `dict`: Ответ в формате JSON.
        """
        payload, headers = self._prepare_payload(signed=signed, params=params, data=data)

        if not signed:
            return await super()._make_request(method=method, url=url, **payload)

        if data:
            return await super()._make_request(
                method=method, url=url, data=payload, headers=headers
            )
        return await super()._make_request(method=method, url=url, params=payload, headers=headers)

    async def request(
        self, method: RequestMethod, url: str, params: dict, data: dict, signed: bool
    ) -> dict:
        """Специальный метод для выполнения запросов на эндпоинты, которые не обернуты в клиенте.

        Параметры:
            method (`str`): HTTP метод ("GET", "POST", "DELETE" и т.д.).
            url (`str`): Полный URL эндпоинта Binance API.
            signed (`bool`): Нужно ли подписывать запрос.
            params (`dict | None`): Query-параметры.
            data (`dict | None`): Тело запроса.

        Возвращает:
            `dict`: Ответ в формате JSON.
        """
        return await self._make_request(method=method, url=url, params=params, signed=signed)

    # topic: general endpoints

    async def ping(self) -> dict:
        """Проверка подключения к REST API.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/general-endpoints#test-connectivity
        """
        url = self._BASE_SPOT_URL + "/api/v3/ping"

        return await self._make_request("GET", url)

    async def server_time(self) -> dict:
        """Получение серверного времени.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/general-endpoints#check-server-time
        """
        url = self._BASE_SPOT_URL + "/api/v3/time"

        return await self._make_request("GET", url)

    async def exchange_info(self) -> dict:
        """Получение информации о символах рынка и текущих правилах биржевой торговли.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/general-endpoints#exchange-information
        """
        url = self._BASE_SPOT_URL + "/api/v3/exchangeInfo"

        return await self._make_request("GET", url)

    # topic: market data endpoints

    async def depth(self, symbol: str, limit: int | None = None) -> dict:
        """Получение книги ордеров.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#order-book
        """
        url = self._BASE_SPOT_URL + "/api/v3/depth"
        params = {"symbol": symbol, "limit": limit}

        return await self._make_request("GET", url, params=params)

    async def trades(self, symbol: str, limit: int | None = None) -> list[dict]:
        """Получение последних сделок.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#recent-trades-list
        """
        url = self._BASE_SPOT_URL + "/api/v3/trades"
        params = {"symbol": symbol, "limit": limit}

        return await self._make_request("GET", url, params=params)

    async def historical_trades(
        self, symbol: str, limit: int | None = None, from_id: int | None = None
    ) -> list[dict]:
        """Исторические сделки.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#old-trade-lookup
        """
        url = self._BASE_SPOT_URL + "/api/v3/historicalTrades"
        params = {"symbol": symbol, "limit": limit, "fromId": from_id}

        return await self._make_request("GET", url, params=params)

    async def agg_trades(
        self,
        symbol: str,
        from_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение агрегированных сделок.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#compressedaggregate-trades-list
        """
        url = self._BASE_SPOT_URL + "/api/v3/aggTrades"
        params = {
            "symbol": symbol,
            "fromId": from_id,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, params=params)

    async def klines(
        self,
        symbol: str,
        interval: str,
        start_time: int | None = None,
        end_time: int | None = None,
        time_zone: str | None = None,
        limit: int | None = None,
    ) -> list[list]:
        """Получение исторических свечей.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#klinecandlestick-data
        """
        url = self._BASE_SPOT_URL + "/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time,
            "timeZone": time_zone,
            "limit": limit,
        }

        return await self._make_request("GET", url, params=params)

    async def ui_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int | None = None,
        end_time: int | None = None,
        time_zone: str | None = None,
        limit: int | None = None,
    ) -> list[list]:
        """Получение UI свечей (оптимизированы для отображения).

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#uiklines
        """
        url = self._BASE_SPOT_URL + "/api/v3/uiKlines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time,
            "timeZone": time_zone,
            "limit": limit,
        }

        return await self._make_request("GET", url, params=params)

    async def avg_price(self, symbol: str) -> dict:
        """Получение текущей средней цены символа.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#current-average-price
        """
        url = self._BASE_SPOT_URL + "/api/v3/avgPrice"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, params=params)

    async def ticker_24hr(
        self,
        symbol: str | None = None,
        symbols: list[str] | None = None,
        type: str | None = None,
    ) -> dict | list[dict]:
        """Получение статистики изменения цен и объема за 24 часа.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#24hr-ticker-price-change-statistics
        """
        url = self._BASE_SPOT_URL + "/api/v3/ticker/24hr"
        params = {"symbol": symbol, "type": type, "symbols": symbols}

        return await self._make_request("GET", url, params=params)

    async def ticker_trading_day(
        self,
        symbol: str | None = None,
        symbols: list[str] | None = None,
        time_zone: str | None = None,
        type: str | None = None,
    ) -> dict | list[dict]:
        """Статистика изменения цен за торговый день.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#trading-day-ticker
        """
        url = self._BASE_SPOT_URL + "/api/v3/ticker/tradingDay"
        params = {
            "symbol": symbol,
            "symbols": symbols,
            "timeZone": time_zone,
            "type": type,
        }

        return await self._make_request("GET", url, params=params)

    async def ticker_price(
        self, symbol: str | None = None, symbols: list[str] | None = None
    ) -> dict | list[dict]:
        """Получение последней цены тикера(ов).

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#symbol-price-ticker
        """
        url = self._BASE_SPOT_URL + "/api/v3/ticker/price"
        params = {"symbol": symbol, "symbols": symbols}

        return await self._make_request("GET", url, params=params)

    async def ticker_book_ticker(
        self, symbol: str | None = None, symbols: list[str] | None = None
    ) -> dict | list[dict]:
        """Получение лучших цен bid/ask в книге ордеров.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#symbol-order-book-ticker
        """
        url = self._BASE_SPOT_URL + "/api/v3/ticker/bookTicker"
        params = {"symbol": symbol, "symbols": symbols}

        return await self._make_request("GET", url, params=params)

    async def ticker(
        self,
        symbol: str | None = None,
        symbols: list[str] | None = None,
        window_size: str | None = None,
        type: str | None = None,
    ) -> dict | list[dict]:
        """Статистика изменения цен в скользящем окне.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#rolling-window-price-change-statistics
        """
        url = self._BASE_SPOT_URL + "/api/v3/ticker"
        params = {
            "symbol": symbol,
            "symbols": symbols,
            "windowSize": window_size,
            "type": type,
        }

        return await self._make_request("GET", url, params=params)

    # topic: trading endpoints

    async def order_create(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: float | None = None,
        quote_order_qty: float | None = None,
        price: float | None = None,
        stop_price: float | None = None,
        time_in_force: str | None = None,
        new_client_order_id: str | None = None,
        iceberg_qty: float | None = None,
        new_order_resp_type: str | None = None,
        self_trade_prevention_mode: str | None = None,
    ) -> dict:
        """Создание нового ордера на спот-рынке.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#new-order-trade
        """
        url = self._BASE_SPOT_URL + "/api/v3/order"
        data = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "quantity": quantity,
            "quoteOrderQty": quote_order_qty,
            "price": price,
            "stopPrice": stop_price,
            "timeInForce": time_in_force,
            "newClientOrderId": new_client_order_id,
            "icebergQty": iceberg_qty,
            "newOrderRespType": new_order_resp_type,
            "selfTradePreventionMode": self_trade_prevention_mode,
        }

        return await self._make_request("POST", url, True, data=data)

    async def order_test(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: float | None = None,
        quote_order_qty: float | None = None,
        price: float | None = None,
        stop_price: float | None = None,
        time_in_force: str | None = None,
        new_client_order_id: str | None = None,
        iceberg_qty: float | None = None,
        new_order_resp_type: str | None = None,
        self_trade_prevention_mode: str | None = None,
    ) -> dict:
        """Тестирование нового ордера (не выполняется реально).

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#test-new-order-trade
        """
        url = self._BASE_SPOT_URL + "/api/v3/order/test"
        data = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "quantity": quantity,
            "quoteOrderQty": quote_order_qty,
            "price": price,
            "stopPrice": stop_price,
            "timeInForce": time_in_force,
            "newClientOrderId": new_client_order_id,
            "icebergQty": iceberg_qty,
            "newOrderRespType": new_order_resp_type,
            "selfTradePreventionMode": self_trade_prevention_mode,
        }

        return await self._make_request("POST", url, True, data=data)

    async def order_cancel(
        self,
        symbol: str,
        order_id: int | None = None,
        orig_client_order_id: str | None = None,
        new_client_order_id: str | None = None,
    ) -> dict:
        """Отмена активного ордера на спот-рынке.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#cancel-order-trade
        """
        url = self._BASE_SPOT_URL + "/api/v3/order"
        data = {
            "symbol": symbol,
            "orderId": order_id,
            "origClientOrderId": orig_client_order_id,
            "newClientOrderId": new_client_order_id,
        }

        return await self._make_request("DELETE", url, True, data=data)

    async def orders_cancel_all(self, symbol: str) -> list[dict]:
        """Отмена всех активных ордеров по символу.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#cancel-all-open-orders-on-a-symbol-trade
        """
        url = self._BASE_SPOT_URL + "/api/v3/openOrders"
        data = {"symbol": symbol}

        return await self._make_request("DELETE", url, True, data=data)

    async def orders_open(self, symbol: str | None = None) -> list[dict]:
        """Получение всех активных ордеров.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#current-open-orders-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/openOrders"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, True, params=params)

    async def oco_order_create(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
        stop_limit_price: float | None = None,
        list_client_order_id: str | None = None,
        limit_client_order_id: str | None = None,
        stop_client_order_id: str | None = None,
        stop_limit_time_in_force: str | None = None,
        new_order_resp_type: str | None = None,
        self_trade_prevention_mode: str | None = None,
        limit_iceberg_qty: float | None = None,
        stop_iceberg_qty: float | None = None,
    ) -> dict:
        """Создание OCO ордера.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#new-oco-trade
        """
        url = self._BASE_SPOT_URL + "/api/v3/order/oco"
        data = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "stopPrice": stop_price,
            "stopLimitPrice": stop_limit_price,
            "listClientOrderId": list_client_order_id,
            "limitClientOrderId": limit_client_order_id,
            "stopClientOrderId": stop_client_order_id,
            "stopLimitTimeInForce": stop_limit_time_in_force,
            "newOrderRespType": new_order_resp_type,
            "selfTradePreventionMode": self_trade_prevention_mode,
            "limitIcebergQty": limit_iceberg_qty,
            "stopIcebergQty": stop_iceberg_qty,
        }

        return await self._make_request("POST", url, True, data=data)

    async def oco_order_cancel(
        self,
        symbol: str,
        order_list_id: int | None = None,
        list_client_order_id: str | None = None,
        new_client_order_id: str | None = None,
    ) -> dict:
        """Отмена OCO ордера.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#cancel-oco-trade
        """
        url = self._BASE_SPOT_URL + "/api/v3/orderList"
        data = {
            "symbol": symbol,
            "orderListId": order_list_id,
            "listClientOrderId": list_client_order_id,
            "newClientOrderId": new_client_order_id,
        }

        return await self._make_request("DELETE", url, True, data=data)

    async def oco_order_get(
        self, order_list_id: int | None = None, orig_client_order_id: str | None = None
    ) -> dict:
        """Получение информации об OCO ордере.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#query-oco-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/orderList"
        params = {
            "orderListId": order_list_id,
            "origClientOrderId": orig_client_order_id,
        }

        return await self._make_request("GET", url, True, params=params)

    async def oco_orders_all(
        self,
        from_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение всех OCO ордеров.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#query-all-oco-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/allOrderList"
        params = {
            "fromId": from_id,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, True, params=params)

    async def oco_orders_open(self) -> list[dict]:
        """Получение активных OCO ордеров.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#query-open-oco-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/openOrderList"

        return await self._make_request("GET", url, True)

    # topic: account endpoints

    async def account(self) -> dict:
        """Получение информации об аккаунте (балансы, комиссии и т.д.).

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/account-endpoints#account-information-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/account"

        return await self._make_request("GET", url, True)

    async def order_get(
        self,
        symbol: str,
        order_id: int | None = None,
        orig_client_order_id: str | None = None,
    ) -> dict:
        """Получение информации об ордере.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#query-order-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/order"
        params = {
            "symbol": symbol,
            "orderId": order_id,
            "origClientOrderId": orig_client_order_id,
        }

        return await self._make_request("GET", url, True, params=params)

    async def all_orders(
        self,
        symbol: str,
        order_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение всех ордеров (активных, отмененных, исполненных) для символа.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#all-orders-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/allOrders"
        params = {
            "symbol": symbol,
            "orderId": order_id,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, True, params=params)

    async def all_open_orders(
        self,
        symbol: str | None = None,
    ) -> list[dict]:
        """Получение всех ордеров активных ордеров.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/account-endpoints#current-open-orders-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/allOrders"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, True, params=params)

    async def my_trades(
        self,
        symbol: str,
        order_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        from_id: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение торговой истории аккаунта.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#account-trade-list-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/myTrades"
        params = {
            "symbol": symbol,
            "orderId": order_id,
            "startTime": start_time,
            "endTime": end_time,
            "fromId": from_id,
            "limit": limit,
        }

        return await self._make_request("GET", url, True, params=params)

    async def order_count_usage(self) -> list[dict]:
        """Получение текущего использования лимитов ордеров.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#query-current-order-count-usage-trade
        """
        url = self._BASE_SPOT_URL + "/api/v3/rateLimit/order"

        return await self._make_request("GET", url, True)

    async def prevented_matches(
        self,
        symbol: str,
        prevented_match_id: int | None = None,
        order_id: int | None = None,
        from_prevented_match_id: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение предотвращенных совпадений.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#query-prevented-matches-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/myPreventedMatches"
        params = {
            "symbol": symbol,
            "preventedMatchId": prevented_match_id,
            "orderId": order_id,
            "fromPreventedMatchId": from_prevented_match_id,
            "limit": limit,
        }

        return await self._make_request("GET", url, True, params=params)

    async def allocations(
        self,
        symbol: str,
        start_time: int | None = None,
        end_time: int | None = None,
        from_allocation_id: int | None = None,
        limit: int | None = None,
        order_id: int | None = None,
    ) -> list[dict]:
        """Получение распределений.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/spot-trading-endpoints#query-allocations-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/myAllocations"
        params = {
            "symbol": symbol,
            "startTime": start_time,
            "endTime": end_time,
            "fromAllocationId": from_allocation_id,
            "limit": limit,
            "orderId": order_id,
        }

        return await self._make_request("GET", url, True, params=params)

    async def commission_rates(self, symbol: str) -> dict:
        """Получение комиссионных ставок.

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/account-endpoints#query-commission-rates-user_data
        """
        url = self._BASE_SPOT_URL + "/api/v3/account/commission"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, True, params=params)

    # topic: futures market data

    async def futures_ping(self) -> dict:
        """Проверка подключения к REST API.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api#api-description
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/ping"

        return await self._make_request("GET", url)

    async def futures_server_time(self) -> dict:
        """Получение текущего времени сервера.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Check-Server-Time#api-description
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/time"

        return await self._make_request("GET", url)

    async def futures_exchange_info(self) -> dict:
        """Получение информации о символах рынка и текущих правилах биржевой торговли.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Exchange-Information#api-description
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/exchangeInfo"

        return await self._make_request("GET", url)

    async def futures_depth(self, symbol: str, limit: int | None = None) -> dict:
        """Получение книги ордеров.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Order-Book#request-parameters
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/depth"
        params = {"symbol": symbol, "limit": limit}

        return await self._make_request("GET", url, params=params)

    async def futures_trades(self, symbol: str, limit: int | None = None) -> list[dict]:
        """Получение последних сделок.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Recent-Trades-List
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/trades"
        params = {"symbol": symbol, "limit": limit}

        return await self._make_request("GET", url, params=params)

    async def futures_historical_trades(
        self, symbol: str, limit: int | None = None, from_id: int | None = None
    ) -> list[dict]:
        """Получение исторических сделок.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Old-Trades-Lookup
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/historicalTrades"
        params = {"symbol": symbol, "limit": limit, "fromId": from_id}

        return await self._make_request("GET", url, params=params)

    async def futures_agg_trades(
        self,
        symbol: str,
        from_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение агрегированных сделок на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Aggregate-Trades-List
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/aggTrades"
        params = {
            "symbol": symbol,
            "fromId": from_id,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, params=params)

    async def futures_ticker_24hr(self, symbol: str | None = None) -> dict | list[dict]:
        """Получение статистики изменения цен и объема за 24 часа.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/24hr-Ticker-Price-Change-Statistics
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/ticker/24hr"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, params=params)

    async def futures_ticker_price(self, symbol: str | None = None) -> dict | list[dict]:
        """Получение последней цены тикера(ов).

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Symbol-Price-Ticker-v2
        """
        url = self._BASE_FUTURES_URL + "/fapi/v2/ticker/price"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, params=params)

    async def futures_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[list]:
        """Получение исторических свечей.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, params=params)

    async def open_interest(self, symbol: str) -> dict:
        """Получение открытого интереса тикера.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/openInterest"
        params = {"symbol": symbol}

        return await self._make_request(method="GET", url=url, params=params)

    async def futures_mark_price(self, symbol: str | None = None) -> dict | list[dict]:
        """Получение ставки финансирования и цены маркировки.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/premiumIndex"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, params=params)

    async def futures_funding_rate(
        self,
        symbol: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение истории ставок финансирования.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/fundingRate"
        params = {
            "symbol": symbol,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, params=params)

    async def futures_funding_info(self) -> list[dict]:
        """Получение информации о ставках финансирования.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Funding-Rate-Info
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/fundingInfo"

        return await self._make_request("GET", url)

    async def open_interest_hist(
        self,
        symbol: str,
        period: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение истории открытого интереса.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics
        """
        url = self._BASE_FUTURES_URL + "/futures/data/openInterestHist"
        params = {
            "symbol": symbol,
            "period": period,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, params=params)

    async def futures_long_short_ratio_accounts(
        self,
        symbol: str,
        period: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение соотношения лонг/шорт по аккаунтам.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Long-Short-Ratio
        """
        url = self._BASE_FUTURES_URL + "/futures/data/topLongShortAccountRatio"
        params = {
            "symbol": symbol,
            "period": period,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, params=params)

    async def futures_long_short_ratio_positions(
        self,
        symbol: str,
        period: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение соотношения лонг/шорт по позициям.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Long-Short-Ratio
        """
        url = self._BASE_FUTURES_URL + "/futures/data/topLongShortPositionRatio"
        params = {
            "symbol": symbol,
            "period": period,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, params=params)

    async def futures_global_long_short_ratio(
        self,
        symbol: str,
        period: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение глобального соотношения лонг/шорт.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Long-Short-Ratio
        """
        url = self._BASE_FUTURES_URL + "/futures/data/globalLongShortAccountRatio"
        params = {
            "symbol": symbol,
            "period": period,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, params=params)

    async def futures_taker_long_short_ratio(
        self,
        symbol: str,
        period: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение соотношения лонг/шорт по тейкерам.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Taker-Buy-Sell-Volume
        """
        url = self._BASE_FUTURES_URL + "/futures/data/takerlongshortRatio"
        params = {
            "symbol": symbol,
            "period": period,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, params=params)

    async def futures_composite_index(self, symbol: str | None = None) -> list[dict]:
        """Получение композитного индекса.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Composite-Index-Symbol-Information
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/indexInfo"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, params=params)

    async def futures_api_trading_status(self) -> dict:
        """Получение статуса торгов API.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Query-Current-API-trading-status
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/apiTradingStatus"

        return await self._make_request("GET", url, True)

    # topic: futures account

    async def futures_account(self) -> dict:
        """Получение информации об аккаунте фьючерсов.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Account-Information-V3
        """
        url = self._BASE_FUTURES_URL + "/fapi/v3/account"
        return await self._make_request("GET", url, True)

    async def futures_balance(self) -> list[dict]:
        """Получение баланса фьючерсного аккаунта.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Futures-Account-Balance-V3
        """
        url = self._BASE_FUTURES_URL + "/fapi/v3/balance"

        return await self._make_request("GET", url, True)

    async def futures_multi_asset_mode(self, multi_assets_margin: bool | None = None) -> dict:
        """Изменение режима мультиактивной маржи.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Change-Multi-Assets-Mode
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/multiAssetsMargin"
        data = {"multiAssetsMargin": multi_assets_margin}

        return await self._make_request("POST", url, True, data=data)

    async def futures_multi_asset_mode_get(self) -> dict:
        """Получение режима мультиактивной маржи.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Get-Current-Multi-Assets-Mode
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/multiAssetsMargin"

        return await self._make_request("GET", url, True)

    # topic: futures trade

    async def futures_order_create(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: float | None = None,
        reduce_only: bool | None = None,
        price: float | None = None,
        new_client_order_id: str | None = None,
        stop_price: float | None = None,
        close_position: bool | None = None,
        activation_price: float | None = None,
        callback_rate: float | None = None,
        time_in_force: str | None = None,
        working_type: str | None = None,
        price_protect: bool | None = None,
        position_side: str | None = None,
        price_match: str | None = None,
        self_trade_prevention_mode: str | None = None,
        good_till_date: int | None = None,
    ) -> dict:
        """Создание нового ордера на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/New-Order
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/order"
        data = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "quantity": quantity,
            "reduceOnly": reduce_only,
            "price": price,
            "newClientOrderId": new_client_order_id,
            "stopPrice": stop_price,
            "closePosition": close_position,
            "activationPrice": activation_price,
            "callbackRate": callback_rate,
            "timeInForce": time_in_force,
            "workingType": working_type,
            "priceProtect": price_protect,
            "positionSide": position_side,
            "priceMatch": price_match,
            "selfTradePreventionMode": self_trade_prevention_mode,
            "goodTillDate": good_till_date,
        }

        return await self._make_request("POST", url, True, data=data)

    async def futures_order_modify(
        self,
        order_id: int | None = None,
        orig_client_order_id: str | None = None,
        symbol: str | None = None,
        side: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        price_match: str | None = None,
    ) -> dict:
        """Изменение ордера на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Modify-Order
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/order"
        data = {
            "orderId": order_id,
            "origClientOrderId": orig_client_order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "priceMatch": price_match,
        }

        return await self._make_request("PUT", url, True, data=data)

    async def futures_order_get(
        self,
        symbol: str,
        order_id: int | None = None,
        orig_client_order_id: str | None = None,
    ) -> dict:
        """Получение информации об ордере на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Query-Order
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/order"
        params = {
            "symbol": symbol,
            "orderId": order_id,
            "origClientOrderId": orig_client_order_id,
        }

        return await self._make_request("GET", url, True, params=params)

    async def futures_orders_open(self, symbol: str | None = None) -> list[dict]:
        """Получение всех активных ордеров на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Current-All-Open-Orders
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/openOrders"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, True, params=params)

    async def futures_orders_all(
        self,
        symbol: str,
        order_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение всех ордеров на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/All-Orders
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/allOrders"
        params = {
            "symbol": symbol,
            "orderId": order_id,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, True, params=params)

    async def futures_orders_cancel_all(self, symbol: str) -> dict:
        """Отмена всех активных ордеров на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Cancel-All-Open-Orders
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/allOpenOrders"
        data = {"symbol": symbol}

        return await self._make_request("DELETE", url, True, data=data)

    async def futures_countdown_cancel_all(
        self,
        symbol: str,
        countdown_time: int,
    ) -> dict:
        """Автоотмена всех активных ордеров через указанное время.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Auto-Cancel-All-Open-Orders
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/countdownCancelAll"
        data = {
            "symbol": symbol,
            "countdownTime": countdown_time,
        }

        return await self._make_request("POST", url, True, data=data)

    async def futures_position_info(self, symbol: str | None = None) -> list[dict]:
        """Получение информации о позициях на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Position-Information-V3
        """
        url = self._BASE_FUTURES_URL + "/fapi/v3/positionRisk"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, True, params=params)

    async def futures_my_trades(
        self,
        symbol: str,
        start_time: int | None = None,
        end_time: int | None = None,
        from_id: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение истории торгов на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Account-Trade-List
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/userTrades"
        params = {
            "symbol": symbol,
            "startTime": start_time,
            "endTime": end_time,
            "fromId": from_id,
            "limit": limit,
        }

        return await self._make_request("GET", url, True, params=params)

    async def futures_income(
        self,
        symbol: str | None = None,
        income_type: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение истории доходов на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Get-Income-History
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/income"
        params = {
            "symbol": symbol,
            "incomeType": income_type,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, True, params=params)

    async def futures_leverage_change(self, symbol: str, leverage: int) -> dict:
        """Изменение кредитного плеча на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Change-Initial-Leverage
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/leverage"
        data = {"symbol": symbol, "leverage": leverage}

        return await self._make_request("POST", url, True, data=data)

    async def futures_margin_type_change(self, symbol: str, margin_type: str) -> dict:
        """Изменение типа маржи на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Change-Margin-Type
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/marginType"
        data = {"symbol": symbol, "marginType": margin_type}

        return await self._make_request("POST", url, True, data=data)

    async def futures_position_margin_modify(
        self,
        symbol: str,
        position_side: str,
        amount: float,
        type: int,
    ) -> dict:
        """Изменение изолированной маржи позиции.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Modify-Isolated-Position-Margin
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/positionMargin"
        data = {
            "symbol": symbol,
            "positionSide": position_side,
            "amount": amount,
            "type": type,
        }

        return await self._make_request("POST", url, True, data=data)

    async def futures_position_margin_history(
        self,
        symbol: str,
        type: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение истории изменений маржи позиции.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Get-Position-Margin-Change-History
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/positionMargin/history"
        params = {
            "symbol": symbol,
            "type": type,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, True, params=params)

    async def futures_commission_rate(self, symbol: str) -> dict:
        """Получение комиссионных ставок на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/User-Commission-Rate
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/commissionRate"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, True, params=params)

    async def futures_adl_quantile(self, symbol: str | None = None) -> list[dict]:
        """Получение информации об автоматической ликвидации.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Position-ADL-Quantile-Estimation
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/adlQuantile"
        params = {"symbol": symbol}

        return await self._make_request("GET", url, True, params=params)

    async def futures_force_orders(
        self,
        symbol: str | None = None,
        auto_close_type: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Получение истории принудительных ордеров пользователя.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/User-s-Force-Orders
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/forceOrders"
        params = {
            "symbol": symbol,
            "autoCloseType": auto_close_type,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        return await self._make_request("GET", url, True, params=params)

    async def futures_api_key_permissions(self) -> dict:
        """Получение разрешений API ключа.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api/Get-API-Key-Permission
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/apiTradingStatus"

        return await self._make_request("GET", url, True)

    async def futures_order_cancel(
        self, symbol: str, order_id: int | None = None, orig_client_order_id: str | None = None
    ) -> dict:
        """Отмена активного ордера на фьючерсном рынке.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Cancel-Order
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/order"
        data = {
            "symbol": symbol,
            "orderId": order_id,
            "origClientOrderId": orig_client_order_id,
        }

        return await self._make_request("DELETE", url, data=data)

    async def futures_batch_orders_create(self, orders: list[dict]) -> list[dict]:
        """Создание множественных ордеров одновременно на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Place-Multiple-Orders
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/batchOrders"
        data = {"batchOrders": json.dumps(orders)}  # Нужен особый дамп

        return await self._make_request("POST", url, signed=True, data=data)

    async def futures_batch_orders_cancel(
        self,
        symbol: str,
        order_id_list: list[int] | None = None,
        orig_client_order_id_list: list[str] | None = None,
    ) -> list[dict]:
        """Отмена множественных ордеров на фьючерсах.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Cancel-Multiple-Orders
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/batchOrders"
        data = {"symbol": symbol}

        if order_id_list:
            data["orderIdList"] = json.dumps(order_id_list)  # Нужен особый дамп

        if orig_client_order_id_list:
            data["origClientOrderIdList"] = json.dumps(  # Нужен особый дамп
                orig_client_order_id_list
            )

        return await self._make_request("DELETE", url, signed=True, data=data)

    # topic: user data streams

    async def listen_key(self) -> dict:
        """Создание ключа прослушивания для подключения к пользовательскому вебсокету.

        https://developers.binance.com/docs/binance-spot-api-docs/testnet/rest-api/user-data-stream-endpoints-deprecated#start-user-data-stream-user_stream-deprecated
        """
        warnings.warn(
            "These requests have been deprecated, which means we will remove them in the future. Please subscribe to the User Data Stream through the WebSocket API instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        url = self._BASE_SPOT_URL + "/api/v3/userDataStream"

        return await super()._make_request("POST", url, headers=self._get_headers())

    async def renew_listen_key(self, listen_key: str) -> dict:
        """Обновление ключа прослушивания для подключения к пользовательскому вебсокету.

        https://developers.binance.com/docs/binance-spot-api-docs/testnet/rest-api/user-data-stream-endpoints-deprecated#keepalive-user-data-stream-user_stream-deprecated
        """
        warnings.warn(
            "These requests have been deprecated, which means we will remove them in the future. Please subscribe to the User Data Stream through the WebSocket API instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        url = self._BASE_SPOT_URL + "/api/v3/userDataStream"
        params = {"listenKey": listen_key}

        return await super()._make_request("PUT", url, params=params, headers=self._get_headers())

    async def close_listen_key(self, listen_key: str) -> dict:
        """Закрытие ключа прослушивания для подключения к пользовательскому вебсокету.

        https://developers.binance.com/docs/binance-spot-api-docs/testnet/rest-api/user-data-stream-endpoints-deprecated#close-user-data-stream-user_stream-deprecated
        """
        warnings.warn(
            "[!IMPORTANT] These requests have been deprecated, which means we will remove them in the future. Please subscribe to the User Data Stream through the WebSocket API instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        url = self._BASE_SPOT_URL + "/api/v3/userDataStream"
        params = {"listenKey": listen_key}

        return await super()._make_request(
            "DELETE", url, params=params, headers=self._get_headers()
        )

    # topic: futures user data streams

    async def futures_listen_key(self) -> dict:
        """Создание ключа прослушивания для подключения к пользовательскому вебсокету.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/user-data-streams/Start-User-Data-Stream#api-description
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/listenKey"

        return await super()._make_request("POST", url, headers=self._get_headers())

    async def futures_renew_listen_key(self) -> dict:
        """Обновление ключа прослушивания для подключения к пользовательскому вебсокету.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/user-data-streams
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/listenKey"

        return await super()._make_request("PUT", url, headers=self._get_headers())

    async def futures_close_listen_key(self) -> dict:
        """Закрытие ключа прослушивания для подключения к пользовательскому вебсокету.

        https://developers.binance.com/docs/derivatives/usds-margined-futures/user-data-streams
        """
        url = self._BASE_FUTURES_URL + "/fapi/v1/listenKey"

        return await super()._make_request("DELETE", url, headers=self._get_headers())
