from typing import Any, Dict, Optional, Tuple, Type, TypeVar, Union

from .dto import merchant_client as mc_dto
from .exceptions import (
    DvNetInvalidResponseDataException, DvNetUndefinedHostException,
    DvNetUndefinedXApiKeyException
)
from .mappers import MerchantMapper

T = TypeVar('T')


class BaseMerchantClient:
    def __init__(
            self,
            mapper: MerchantMapper,
            host: Optional[str] = None,
            x_api_key: Optional[str] = None
    ):
        self._mapper = mapper
        self._host = host
        self._x_api_key = x_api_key

    def _get_actual_request_params(
            self, x_api_key: Optional[str], host: Optional[str]
    ) -> Tuple[str, str]:
        resolved_host = host or self._host
        if not resolved_host:
            raise DvNetUndefinedHostException(
                "Please set host in client, or pass it in parameters"
            )

        resolved_x_api_key = x_api_key or self._x_api_key
        if not resolved_x_api_key:
            raise DvNetUndefinedXApiKeyException(
                "Please set x-api-key in client, or pass it in parameters"
            )

        return resolved_host, resolved_x_api_key

    def _process_response(
            self, response_data: Union[Dict[str, Any], str], expected_type: Type[T]
    ) -> T:
        if not isinstance(response_data, dict) or 'data' not in response_data:
            raise DvNetInvalidResponseDataException(
                "The response does not contain a 'data' key."
            )

        data = response_data['data']

        try:
            mapper_method_map = {
                mc_dto.TotalExchangeBalanceResponse: self._mapper.make_total_exchange_balance,
                mc_dto.ExternalAddressesResponse: self._mapper.make_external_addresses,
                mc_dto.ProcessingWalletsBalancesResponse: self._mapper.make_processing_wallets_balances,
                mc_dto.CurrenciesResponse: self._mapper.make_currencies,
                mc_dto.CurrencyRateResponse: self._mapper.make_currency_rate,
                mc_dto.ProcessingWithdrawalResponse: self._mapper.make_processing_withdrawal,
                mc_dto.WithdrawalResponse: self._mapper.make_withdrawal,
            }

            if expected_type in mapper_method_map:
                return mapper_method_map[expected_type](data)  # type: ignore

            if expected_type == list and all(isinstance(i, dict) for i in data):
                return [self._mapper.make_account(item) for item in data]  # type: ignore

            raise DvNetInvalidResponseDataException(f"No mapper found for type {expected_type}")

        except (KeyError, TypeError) as e:
            raise DvNetInvalidResponseDataException(f"Failed to map response data: {e}") from e
