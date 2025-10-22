from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class CurrencyShortDto:
    id: str
    code: str
    name: str
    blockchain: str


@dataclass
class AccountDto:
    balance: str
    balance_usd: str
    count: int
    count_with_balance: int
    currency: CurrencyShortDto


@dataclass
class AddressDto:
    id: str
    wallet_id: str
    user_id: str
    currency_id: str
    blockchain: str
    address: str
    dirty: bool


@dataclass
class AssetDto:
    identity: str
    amount: str
    amount_usd: str


@dataclass
class BalanceDto:
    native_token: str
    native_token_usd: str


@dataclass
class TronDataDto:
    available_bandwidth_for_use: str
    available_energy_for_use: str
    stacked_bandwidth: str
    stacked_bandwidth_trx: str
    stacked_energy: str
    stacked_energy_trx: str
    stacked_trx: str
    total_bandwidth: str
    total_energy: str
    total_used_bandwidth: str
    total_used_energy: str


@dataclass
class BlockchainAdditionalDataDto:
    tron_data: TronDataDto


@dataclass
class IconDto:
    icon_128: str
    icon_512: str
    icon_svg: str


@dataclass
class CurrencyDto:
    id: str
    blockchain: str
    code: str
    contract_address: str
    has_balance: bool
    icon: IconDto
    blockchain_icon: IconDto
    is_fiat: bool
    min_confirmation: int
    name: str
    precision: int
    status: bool
    withdrawal_min_balance: str
    explorer_link: str


@dataclass
class ExchangeBalanceDto:
    amount: str
    amount_usd: str
    currency: str


@dataclass
class ProcessingWalletBalanceDto:
    address: str
    blockchain: str
    asset: List[AssetDto]
    currency: CurrencyShortDto
    balance: BalanceDto
    additional_data: Optional[BlockchainAdditionalDataDto]


@dataclass
class TransferDto:
    kind: str
    stage: str
    status: str


@dataclass
class CurrenciesResponse:
    currencies: List[CurrencyDto]


@dataclass
class CurrencyRateResponse:
    code: str
    rate: str
    rate_source: str


@dataclass
class ExternalAddressesResponse:
    address: List[AddressDto]
    created_at: datetime
    id: str
    pay_url: str
    store_external_id: str
    store_id: str
    updated_at: datetime
    rates: List[str]
    amount_usd: str


@dataclass
class ProcessingWalletsBalancesResponse:
    balances: List[ProcessingWalletBalanceDto]


@dataclass
class ProcessingWithdrawalResponse:
    address_from: str
    address_to: str
    amount: str
    amount_usd: str
    created_at: datetime
    currency_id: str
    store_id: str
    transfer: Optional[TransferDto]
    tx_hash: str


@dataclass
class TotalExchangeBalanceResponse:
    total_usd: str
    exchange_balance: List[ExchangeBalanceDto]


@dataclass
class WithdrawalResponse:
    address_from: str
    address_to: str
    amount: str
    amount_usd: str
    created_at: datetime
    currency_id: str
    id: str
    store_id: str
    transfer_id: Optional[str]
