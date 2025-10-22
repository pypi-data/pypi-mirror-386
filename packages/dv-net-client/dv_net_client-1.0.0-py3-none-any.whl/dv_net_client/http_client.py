import asyncio
import json
from typing import Any, Dict, Optional, Tuple, Union, Protocol, runtime_checkable
from urllib import request
from urllib.error import HTTPError, URLError

from .exceptions import (
    DvNetInvalidRequestException, DvNetNetworkException, DvNetServerException
)


@runtime_checkable
class HttpClient(Protocol):
    def send_request(
            self,
            method: str,
            url: str,
            headers: Dict[str, str],
            data: Optional[Dict[str, Any]] = None,
            timeout: int = 30
    ) -> Tuple[int, Union[Dict[str, Any], str]]:
        ...


@runtime_checkable
class AsyncHttpClient(Protocol):
    async def send_request(
            self,
            method: str,
            url: str,
            headers: Dict[str, str],
            data: Optional[Dict[str, Any]] = None,
            timeout: int = 30
    ) -> Tuple[int, Union[Dict[str, Any], str]]:
        ...


class UrllibHttpClient:
    def send_request(
            self,
            method: str,
            url: str,
            headers: Dict[str, str],
            data: Optional[Dict[str, Any]] = None,
            timeout: int = 30
    ) -> Tuple[int, Union[Dict[str, Any], str]]:
        body = json.dumps(data).encode('utf-8') if data else None
        req = request.Request(url, data=body, headers=headers, method=method)

        try:
            with request.urlopen(req, timeout=timeout) as response:
                status_code = response.status
                response_body = response.read().decode('utf-8')
        except HTTPError as e:
            response_body = e.read().decode('utf-8', errors='ignore')
            if 400 <= e.code < 500:
                raise DvNetInvalidRequestException(
                    "Client error", response_body, e.code
                ) from e
            if 500 <= e.code < 600:
                raise DvNetServerException(
                    "Server error", response_body, e.code
                ) from e
            raise DvNetNetworkException(f"HTTP Error: {e.code}") from e
        except URLError as e:
            raise DvNetNetworkException(f"URL Error: {e.reason}") from e
        except Exception as e:
            raise DvNetNetworkException(f"An unexpected error occurred: {e}") from e

        try:
            return status_code, json.loads(response_body)
        except json.JSONDecodeError:
            return status_code, response_body


class AiohttpHttpClient:
    def __init__(self):
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp is not installed. Please install it with 'pip install aiohttp'")
        self.aiohttp = aiohttp

    async def send_request(
            self,
            method: str,
            url: str,
            headers: Dict[str, str],
            data: Optional[Dict[str, Any]] = None,
            timeout: int = 30
    ) -> Tuple[int, Union[Dict[str, Any], str]]:
        try:
            async with self.aiohttp.ClientSession(timeout=self.aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.request(
                        method, url, json=data, headers=headers
                ) as response:
                    status_code = response.status
                    response_text = await response.text()

                    if 400 <= status_code < 500:
                        raise DvNetInvalidRequestException(
                            "Client error", response_text, status_code
                        )
                    if 500 <= status_code < 600:
                        raise DvNetServerException(
                            "Server error", response_text, status_code
                        )

                    if not response.ok:
                        raise DvNetNetworkException(f"HTTP Error: {status_code}")

                    try:
                        return status_code, await response.json()
                    except (json.JSONDecodeError, self.aiohttp.ContentTypeError):
                        return status_code, response_text
        except asyncio.TimeoutError as e:
            raise DvNetNetworkException("Request timed out") from e
        except self.aiohttp.ClientError as e:
            raise DvNetNetworkException(f"Aiohttp client error: {e}") from e
