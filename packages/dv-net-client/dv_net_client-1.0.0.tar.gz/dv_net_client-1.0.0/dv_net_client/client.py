from typing import Dict, List, Optional, Any

from ._base_client import BaseMerchantClient
from .dto import merchant_client as mc_dto
from .http_client import HttpClient, UrllibHttpClient
from .mappers import MerchantMapper


class MerchantClient(BaseMerchantClient):
    def __init__(
            self,
            http_client: Optional[HttpClient] = None,
            host: Optional[str] = None,
            x_api_key: Optional[str] = None
    ):
        super().__init__(MerchantMapper(), host, x_api_key)
        self._http_client = http_client or UrllibHttpClient()

    def _send_request(
            self,
            method: str,
            uri: str,
            data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None
    ) -> Any:
        _, response_data = self._http_client.send_request(
            method=method,
            url=uri,
            data=data,
            headers=headers or {}
        )
        return response_data

    def get_exchange_balances(
            self, x_api_key: Optional[str] = None, host: Optional[str] = None
    ) -> mc_dto.TotalExchangeBalanceResponse:
        host, x_api_key = self._get_actual_request_params(x_api_key, host)
        uri = f"{host}/api/v1/external/exchange-balances"
        headers = {'x-api-key': x_api_key}
        response = self._send_request('GET', uri, headers=headers)
        return self._process_response(response, mc_dto.TotalExchangeBalanceResponse)

    def get_external_wallet(
            self,
            store_external_id: str,
            email: Optional[str] = None,
            ip: Optional[str] = None,
            amount: Optional[str] = None,
            currency: Optional[str] = None,
            x_api_key: Optional[str] = None,
            host: Optional[str] = None
    ) -> mc_dto.ExternalAddressesResponse:
        host, x_api_key = self._get_actual_request_params(x_api_key, host)
        uri = f"{host}/api/v1/external/wallet"
        payload = {
            'email': email,
            'ip': ip,
            'store_external_id': store_external_id,
            'amount': amount,
            'currency': currency,
        }
        data = {k: v for k, v in payload.items() if v is not None}
        headers = {'Content-Type': 'application/json', 'x-api-key': x_api_key}
        response = self._send_request('POST', uri, data=data, headers=headers)
        return self._process_response(response, mc_dto.ExternalAddressesResponse)

    def get_processing_wallets_balances(
            self, x_api_key: Optional[str] = None, host: Optional[str] = None
    ) -> mc_dto.ProcessingWalletsBalancesResponse:
        host, x_api_key = self._get_actual_request_params(x_api_key, host)
        uri = f"{host}/api/v1/external/processing-wallet-balances"
        headers = {'x-api-key': x_api_key}
        response = self._send_request('GET', uri, headers=headers)
        return self._process_response(response, mc_dto.ProcessingWalletsBalancesResponse)

    def get_store_currencies(
            self, x_api_key: Optional[str] = None, host: Optional[str] = None
    ) -> mc_dto.CurrenciesResponse:
        host, x_api_key = self._get_actual_request_params(x_api_key, host)
        uri = f"{host}/api/v1/external/store/currencies"
        headers = {'x-api-key': x_api_key}
        response = self._send_request('GET', uri, headers=headers)
        return self._process_response(response, mc_dto.CurrenciesResponse)

    def get_store_currency_rate(
            self, currency_id: str, x_api_key: Optional[str] = None, host: Optional[str] = None
    ) -> mc_dto.CurrencyRateResponse:
        host, x_api_key = self._get_actual_request_params(x_api_key, host)
        uri = f"{host}/api/v1/external/store/currencies/{currency_id}/rate"
        headers = {'x-api-key': x_api_key}
        response = self._send_request('GET', uri, headers=headers)
        return self._process_response(response, mc_dto.CurrencyRateResponse)

    def get_withdrawal_processing_status(
            self, withdrawal_id: str, x_api_key: Optional[str] = None, host: Optional[str] = None
    ) -> mc_dto.ProcessingWithdrawalResponse:
        host, x_api_key = self._get_actual_request_params(x_api_key, host)
        uri = f"{host}/api/v1/external/withdrawal-from-processing/{withdrawal_id}"
        headers = {'x-api-key': x_api_key}
        response = self._send_request('GET', uri, headers=headers)
        return self._process_response(response, mc_dto.ProcessingWithdrawalResponse)

    def initialize_transfer(
            self,
            address_to: str,
            currency_id: str,
            amount: str,
            request_id: str,
            x_api_key: Optional[str] = None,
            host: Optional[str] = None
    ) -> mc_dto.WithdrawalResponse:
        host, x_api_key = self._get_actual_request_params(x_api_key, host)
        uri = f"{host}/api/v1/external/withdrawal-from-processing"
        data = {
            'address_to': address_to,
            'currency_id': currency_id,
            'amount': amount,
            'request_id': request_id,
        }
        headers = {'Content-Type': 'application/json', 'x-api-key': x_api_key}
        response = self._send_request('POST', uri, data=data, headers=headers)
        return self._process_response(response, mc_dto.WithdrawalResponse)

    def get_hot_wallet_balances(
            self, x_api_key: Optional[str] = None, host: Optional[str] = None
    ) -> List[mc_dto.AccountDto]:
        host, x_api_key = self._get_actual_request_params(x_api_key, host)
        uri = f"{host}/api/v1/external/wallet/balance/hot"
        headers = {'Content-Type': 'application/json', 'x-api-key': x_api_key}
        response = self._send_request('GET', uri, headers=headers)
        return self._process_response(response, list)  # type: ignore

    def delete_withdrawal_from_processing(
            self, withdrawal_id: str, x_api_key: Optional[str] = None, host: Optional[str] = None
    ) -> None:
        host, x_api_key = self._get_actual_request_params(x_api_key, host)
        uri = f"{host}/api/v1/external/withdrawal-from-processing/{withdrawal_id}"
        headers = {'x-api-key': x_api_key}
        self._send_request('DELETE', uri, headers=headers)
