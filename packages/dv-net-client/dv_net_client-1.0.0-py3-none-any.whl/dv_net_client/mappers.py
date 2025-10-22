from datetime import datetime
from typing import Any, Dict, List

from .dto import merchant_client as mc_dto, webhook as wh_dto
from .exceptions import DvNetInvalidWebhookException


def _parse_datetime(dt_str: Any) -> datetime:
    if not isinstance(dt_str, str):
        raise TypeError(f"Expected string, but got {type(dt_str)}")
    # Remove nanoseconds and timezone information for compatibility
    if '.' in dt_str:
        dt_str = dt_str.split('.')[0]
    if '+' in dt_str:
        dt_str = dt_str.split('+')[0]
    if 'Z' in dt_str:
        dt_str = dt_str.replace('Z', '')

    return datetime.fromisoformat(dt_str)


class MerchantMapper:
    def make_icon(self, data: Dict[str, Any]) -> mc_dto.IconDto:
        return mc_dto.IconDto(
            icon_128=data['icon_128'],
            icon_512=data['icon_512'],
            icon_svg=data['icon_svg'],
        )

    def make_currency_short(self, data: Dict[str, Any]) -> mc_dto.CurrencyShortDto:
        return mc_dto.CurrencyShortDto(
            id=data['id'],
            code=data['code'],
            name=data['name'],
            blockchain=data['blockchain'],
        )

    def make_account(self, data: Dict[str, Any]) -> mc_dto.AccountDto:
        return mc_dto.AccountDto(
            balance=data['balance'],
            balance_usd=data['balance_usd'],
            count=data['count'],
            count_with_balance=data['count_with_balance'],
            currency=self.make_currency_short(data['currency']),
        )

    def make_exchange_balance(self, data: Dict[str, Any]) -> mc_dto.ExchangeBalanceDto:
        return mc_dto.ExchangeBalanceDto(
            amount=data['amount'],
            amount_usd=data['amount_usd'],
            currency=data['currency'],
        )

    def make_total_exchange_balance(self, data: Dict[str, Any]) -> mc_dto.TotalExchangeBalanceResponse:
        return mc_dto.TotalExchangeBalanceResponse(
            total_usd=data['total_usd'],
            exchange_balance=[self.make_exchange_balance(item) for item in data['balances']],
        )

    def make_address(self, data: Dict[str, Any]) -> mc_dto.AddressDto:
        return mc_dto.AddressDto(
            id=data['id'],
            wallet_id=data['wallet_id'],
            user_id=data['user_id'],
            currency_id=data['currency_id'],
            blockchain=data['blockchain'],
            address=data['address'],
            dirty=data['dirty'],
        )

    def make_external_addresses(self, data: Dict[str, Any]) -> mc_dto.ExternalAddressesResponse:
        return mc_dto.ExternalAddressesResponse(
            address=[self.make_address(item) for item in data['address']],
            created_at=_parse_datetime(data['created_at']),
            id=data['id'],
            pay_url=data['pay_url'],
            store_external_id=data['store_external_id'],
            store_id=data['store_id'],
            updated_at=_parse_datetime(data['updated_at']),
            rates=data['rates'],
            amount_usd=data['amount_usd'],
        )

    def make_asset(self, data: Dict[str, Any]) -> mc_dto.AssetDto:
        return mc_dto.AssetDto(
            identity=data['identity'],
            amount=data['amount'],
            amount_usd=data['amount_usd'],
        )

    def make_balance(self, data: Dict[str, Any]) -> mc_dto.BalanceDto:
        return mc_dto.BalanceDto(
            native_token=data['native_token'],
            native_token_usd=data['native_token_usd'],
        )

    def make_tron_data(self, data: Dict[str, Any]) -> mc_dto.TronDataDto:
        return mc_dto.TronDataDto(
            available_bandwidth_for_use=data['available_bandwidth_for_use'],
            available_energy_for_use=data['available_energy_for_use'],
            stacked_bandwidth=data['stacked_bandwidth'],
            stacked_bandwidth_trx=data['stacked_bandwidth_trx'],
            stacked_energy=data['stacked_energy'],
            stacked_energy_trx=data['stacked_energy_trx'],
            stacked_trx=data['stacked_trx'],
            total_bandwidth=data['total_bandwidth'],
            total_energy=data['total_energy'],
            total_used_bandwidth=data['total_used_bandwidth'],
            total_used_energy=data['total_used_energy'],
        )

    def make_blockchain_additional_data(self, data: Dict[str, Any]) -> mc_dto.BlockchainAdditionalDataDto:
        return mc_dto.BlockchainAdditionalDataDto(
            tron_data=self.make_tron_data(data['tron_data'])
        )

    def make_processing_wallet_balance(self, data: Dict[str, Any]) -> mc_dto.ProcessingWalletBalanceDto:
        additional_data = None
        if 'additional_data' in data and data['additional_data'] and 'tron_data' in data['additional_data']:
            additional_data = self.make_blockchain_additional_data(data['additional_data'])

        return mc_dto.ProcessingWalletBalanceDto(
            address=data['address'],
            blockchain=data['blockchain'],
            asset=[self.make_asset(item) for item in data['assets']],
            currency=self.make_currency_short(data['currency']),
            balance=self.make_balance(data['balance']),
            additional_data=additional_data,
        )

    def make_processing_wallets_balances(self, data: List[Dict[str, Any]]) -> mc_dto.ProcessingWalletsBalancesResponse:
        return mc_dto.ProcessingWalletsBalancesResponse(
            balances=[self.make_processing_wallet_balance(item) for item in data]
        )

    def make_currency(self, data: Dict[str, Any]) -> mc_dto.CurrencyDto:
        return mc_dto.CurrencyDto(
            id=data['id'],
            blockchain=data['blockchain'],
            code=data['code'],
            contract_address=data['contract_address'],
            has_balance=data['has_balance'],
            icon=self.make_icon(data['icon']),
            blockchain_icon=self.make_icon(data['blockchain_icon']),
            is_fiat=data['is_fiat'],
            min_confirmation=data['min_confirmation'],
            name=data['name'],
            precision=data['precision'],
            status=data['status'],
            withdrawal_min_balance=data['withdrawal_min_balance'],
            explorer_link=data['explorer_link'],
        )

    def make_currencies(self, data: List[Dict[str, Any]]) -> mc_dto.CurrenciesResponse:
        return mc_dto.CurrenciesResponse(
            currencies=[self.make_currency(item) for item in data]
        )

    def make_currency_rate(self, data: Dict[str, Any]) -> mc_dto.CurrencyRateResponse:
        return mc_dto.CurrencyRateResponse(
            code=data['code'],
            rate=data['rate'],
            rate_source=data['rate_source'],
        )

    def make_transfer(self, data: Dict[str, Any]) -> mc_dto.TransferDto:
        return mc_dto.TransferDto(
            kind=data['kind'],
            stage=data['stage'],
            status=data['status'],
        )

    def make_processing_withdrawal(self, data: Dict[str, Any]) -> mc_dto.ProcessingWithdrawalResponse:
        transfer = self.make_transfer(data['transfer']) if 'transfer' in data and data['transfer'] else None
        return mc_dto.ProcessingWithdrawalResponse(
            address_from=data['address_from'],
            address_to=data['address_to'],
            amount=data['amount'],
            amount_usd=data['amount_usd'],
            created_at=_parse_datetime(data['created_at']),
            currency_id=data['currency_id'],
            store_id=data['store_id'],
            transfer=transfer,
            tx_hash=data['tx_hash'],
        )

    def make_withdrawal(self, data: Dict[str, Any]) -> mc_dto.WithdrawalResponse:
        return mc_dto.WithdrawalResponse(
            address_from=data['address_from'],
            address_to=data['address_to'],
            amount=data['amount'],
            amount_usd=data['amount_usd'],
            created_at=_parse_datetime(data['created_at']),
            currency_id=data['currency_id'],
            id=data['id'],
            store_id=data['store_id'],
            transfer_id=data.get('transfer_id'),
        )


class WebhookMapper:
    def _make_transaction(self, data: Dict[str, Any], prefix: str = "") -> wh_dto.TransactionDto:
        return wh_dto.TransactionDto(
            tx_id=data[f'{prefix}tx_id'],
            tx_hash=data[f'{prefix}tx_hash'],
            bc_uniq_key=data[f'{prefix}bc_uniq_key'],
            created_at=_parse_datetime(data[f'{prefix}created_at']),
            currency=data[f'{prefix}currency'],
            currency_id=data[f'{prefix}currency_id'],
            blockchain=data[f'{prefix}blockchain'],
            amount=data[f'{prefix}amount'],
            amount_usd=data[f'{prefix}amount_usd'],
        )

    def _make_wallet(self, data: Dict[str, Any], prefix: str = "") -> wh_dto.WalletDto:
        return wh_dto.WalletDto(
            id=data[f'{prefix}id'],
            store_external_id=data[f'{prefix}store_external_id'],
        )

    def map_webhook(self, data: Dict[str, Any]) -> Any:
        try:
            if 'withdrawal_id' in data:
                return self._make_withdrawal_webhook(data)
            if 'type' in data:
                return self._make_confirmed_webhook(data)
            if 'unconfirmed_type' in data:
                return self._make_unconfirmed_webhook(data)
        except (KeyError, TypeError) as e:
            raise DvNetInvalidWebhookException(f"Cannot map webhook: {e}") from e

        raise DvNetInvalidWebhookException(
            'Invalid webhook format, missing "type", "withdrawal_id" or "unconfirmed_type" field'
        )

    def _make_withdrawal_webhook(self, data: Dict[str, Any]) -> wh_dto.WithdrawalWebhookResponse:
        return wh_dto.WithdrawalWebhookResponse(
            type=data['type'],
            created_at=_parse_datetime(data['created_at']),
            paid_at=_parse_datetime(data['paid_at']),
            amount=data['amount'],
            transactions=self._make_transaction(data['transactions']),
            withdrawal_id=data['withdrawal_id'],
        )

    def _make_confirmed_webhook(self, data: Dict[str, Any]) -> wh_dto.ConfirmedWebhookResponse:
        return wh_dto.ConfirmedWebhookResponse(
            type=data['type'],
            status=data['status'],
            created_at=_parse_datetime(data['created_at']),
            paid_at=_parse_datetime(data['paid_at']),
            amount=data['amount'],
            transactions=self._make_transaction(data['transactions']),
            wallet=self._make_wallet(data['wallet']),
        )

    def _make_unconfirmed_webhook(self, data: Dict[str, Any]) -> wh_dto.UnconfirmedWebhookResponse:
        return wh_dto.UnconfirmedWebhookResponse(
            type=data['unconfirmed_type'],
            status=data['unconfirmed_status'],
            created_at=_parse_datetime(data['unconfirmed_created_at']),
            paid_at=_parse_datetime(data['unconfirmed_paid_at']),
            amount=data['unconfirmed_amount'],
            transactions=self._make_transaction(data['unconfirmed_transactions'], 'unconfirmed_'),
            wallet=self._make_wallet(data['unconfirmed_wallet'], 'unconfirmed_'),
        )
