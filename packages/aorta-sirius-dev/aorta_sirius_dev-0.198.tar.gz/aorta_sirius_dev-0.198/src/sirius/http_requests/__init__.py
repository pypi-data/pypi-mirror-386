import json
from abc import abstractmethod
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Dict, Any, List, cast

import httpx
from httpx import Response, Cookies, Headers, URL, AsyncClient
from httpx._types import RequestFiles
from pydantic import BaseModel

from sirius import common
from sirius.common import DataClass
from sirius.http_requests.exceptions import ClientSideException, ServerSideException


@dataclass
class HTTPResponse:
    response: Response
    response_code: int
    is_successful: bool
    headers: Headers
    data: Dict[Any, Any] | None = None
    response_text: str | None = None
    cookies: Cookies | None = None

    def __init__(self, response: Response, *args: List[Any], **kwargs: Dict[str, Any]) -> None:
        self.response = response
        self.response_code = self.response.status_code
        self.is_successful = 200 <= self.response_code < 300
        self.response_text = self.response.text
        self.headers = response.headers
        self.cookies = response.cookies

        if self.response_text is not None and self.response_text != "":
            try:
                self.data = self.response.json()
            except JSONDecodeError:
                self.data = None

        super().__init__(*args, **kwargs)


class HTTPSession:
    host: str

    @staticmethod
    def raise_http_exception(http_response: HTTPResponse) -> None:
        error_message: str = f"HTTP Exception\n" \
                             f"URL: {str(http_response.response.url)}\n" \
                             f"Headers: {str(http_response.headers)}\n" \
                             f"Method: {http_response.response.request.method.upper()}\n" \
                             f"Response Code: {http_response.response_code}\n" \
                             f"Response Text: {http_response.response_text}"

        if 400 <= http_response.response_code < 500:
            raise ClientSideException(error_message, data={"http_response": http_response})
        else:
            raise ServerSideException(error_message, data={"http_response": http_response})


class AsyncHTTPSession(HTTPSession):
    client: AsyncClient
    _instance_list: List["AsyncHTTPSession"] = []

    def __new__(cls, url_str: str, headers: Dict[str, Any] | None = None) -> "AsyncHTTPSession":
        host: str = URL(url_str).host
        instance: AsyncHTTPSession | None = None

        for i in cls._instance_list:
            if i.host == host and (headers is None or common.is_dict_include_another_dict(cast(Dict[str, Any], headers), dict(i.client.headers))):
                instance = i

        if instance is None:
            instance = super().__new__(cls)
            instance.host = host
            instance.client = httpx.AsyncClient()

            if headers is not None:
                instance.client.headers.update(headers)

            cls._instance_list.append(instance)

        if instance.client.is_closed:
            instance.client = httpx.AsyncClient()

        return instance

    async def get(self, url: str, query_params: Dict[str, Any] | None = None, headers: Dict[str, Any] | None = None) -> HTTPResponse:
        http_response: HTTPResponse = HTTPResponse(await self.client.get(url, params=query_params, headers=headers))
        if not http_response.is_successful:
            AsyncHTTPSession.raise_http_exception(http_response)

        return http_response

    async def put(self, url: str, data: Dict[str, Any], headers: Dict[str, Any] | None = None, files: RequestFiles | None = None) -> HTTPResponse:
        headers = {} if not headers else headers
        headers.setdefault("content-type", "application/json")
        data_string: str | None = json.dumps(data) if data else None
        http_response: HTTPResponse = HTTPResponse(await self.client.put(url, data=data_string, headers=headers, files=files))  # type: ignore[arg-type]

        if not http_response.is_successful:
            AsyncHTTPSession.raise_http_exception(http_response)

        return http_response

    async def post(self, url: str, data: Dict[str, Any] | None = None, headers: Dict[str, Any] | None = None, files: RequestFiles | None = None) -> HTTPResponse:
        headers = {} if not headers else headers

        if files:
            http_response = HTTPResponse(await self.client.post(url, data=data, files=files, headers=headers))
        else:
            data_string: str | None = json.dumps(data) if data else None
            headers.setdefault("content-type", "application/json")
            http_response = HTTPResponse(await self.client.post(url, data=data_string, files=files, headers=headers))  # type: ignore[arg-type]

        if not http_response.is_successful:
            self.raise_http_exception(http_response)

        return http_response

    async def delete(self, url: str, headers: Dict[str, Any] | None = None) -> HTTPResponse:
        http_response: HTTPResponse = HTTPResponse(await self.client.delete(url, headers=headers))
        if not http_response.is_successful:
            AsyncHTTPSession.raise_http_exception(http_response)

        return http_response


class HTTPModel(DataClass):

    @abstractmethod
    def __init__(self, **data: Any):
        super().__init__(**data)

    @staticmethod
    async def get_one(cls: type, url: str, query_params: Dict[str, Any] | None = None, http_session: AsyncHTTPSession | None = None) -> DataClass:
        if http_session is None:
            http_session = AsyncHTTPSession(url)

        if not issubclass(cls, BaseModel):
            raise ServerSideException(f"{cls.__name__} is not a Pydantic subclass")

        response: HTTPResponse = await http_session.get(url=url, query_params=query_params)
        return cls(**response.data)  # type: ignore[return-value]

    @staticmethod
    async def get_multiple(cls: type, url: str, query_params: Dict[str, Any] | None = None, headers: Dict[str, Any] | None = None, http_session: AsyncHTTPSession | None = None) -> List[DataClass]:
        if http_session is None:
            http_session = AsyncHTTPSession(url)

        if not issubclass(cls, BaseModel):
            raise ServerSideException(f"{cls.__name__} is not a Pydantic subclass")

        response: HTTPResponse = await http_session.get(url=url, query_params=query_params, headers=headers)
        return [cls(**data) for data in response.data]  # type: ignore[misc]

    @staticmethod
    async def post_return_one(cls: type, url: str, data: Dict[Any, Any] | None = None, headers: Dict[str, Any] | None = None, http_session: AsyncHTTPSession | None = None) -> DataClass:
        if http_session is None:
            http_session = AsyncHTTPSession(url)

        if not issubclass(cls, BaseModel):
            raise ServerSideException(f"{cls.__name__} is not a Pydantic subclass")

        response: HTTPResponse = await http_session.post(url=url, data=data, headers=headers)
        return cls(**response.data)  # type: ignore[return-value]
