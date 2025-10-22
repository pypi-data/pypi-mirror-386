# DV.net Python Client

A Python client for DV.net API integration.

## Documentation

You can find extended documentation at https://docs.dv.net/

## Installation

```bash
pip install dv-net-client
# For the async client, also install aiohttp
pip install aiohttp
```

## Setup

### Synchronous Client
```python
from dv_net_client.client import MerchantClient
# Initialize the client with host and API key
client = MerchantClient(
    host='[https://api.example.com](https://api.example.com)', # Your DV.net API host
    x_api_key='your-api-key'
)

# You can also pass the host and key in each request
# client = MerchantClient()
# client.get_exchange_balances(host='...', x_api_key='...')
```

### Asynchronous Client
```python
import asyncio
from dv_net_client.async_client import AsyncMerchantClient

async def main():
    # Initialize the client
    async_client = AsyncMerchantClient(
        host='[https://api.example.com](https://api.example.com)',
        x_api_key='your-api-key'
    )
    
    # Example call
    balances = await async_client.get_exchange_balances()
    print(balances)

if __name__ == "__main__":
    asyncio.run(main())
```

## Usage

### Signature Verification

Verify the authenticity of webhook signatures.
```python
from dv_net_client.utils import MerchantUtilsManager

manager = MerchantUtilsManager()
is_valid = manager.check_sign(
    client_signature='received-signature-hash',
    client_key='your-client-key',
    request_body={'data': 'request-payload'}
)
# Returns True if the signature is valid
```

### Webhook Processing
```python
from dv_net_client.mappers import WebhookMapper

mapper = WebhookMapper()
webhook_data = {'type': 'PaymentReceived', ...} # your webhook data
webhook_dto = mapper.map_webhook(webhook_data)
# Returns a ConfirmedWebhookResponse, UnconfirmedWebhookResponse, or WithdrawalWebhookResponse object
```

### API Call Examples (Synchronous Client)

All methods of the synchronous client have asynchronous counterparts in AsyncMerchantClient.

#### Get Exchange Balances:

```python
balances = client.get_exchange_balances()
# Returns a TotalExchangeBalanceResponse object
```

#### Create External Wallet:
```python
wallet = client.get_external_wallet(
    store_external_id='store-123',
    email='user@example.com',
    ip='127.0.0.1',
    amount='100.00',
    currency='USD'
)
# Returns an ExternalAddressesResponse object
```

#### Initialize Withdrawal:
```python
withdrawal = client.initialize_transfer(
    address_to='0x123...',
    currency_id='ETH',
    amount='1.5',
    request_id='unique-request-id'
)
# Returns a WithdrawalResponse object
```