# Official Fireblocks Python SDK
[![PyPI version](https://badge.fury.io/py/fireblocks.svg)](https://badge.fury.io/py/fireblocks)

The Fireblocks SDK allows developers to seamlessly integrate with the Fireblocks platform and perform a variety of operations, including managing vault accounts and executing transactions securely.

For detailed API documentation please refer to the [Fireblocks API Reference](https://developers.fireblocks.com/reference/).

## Requirements.

Python 3.8+

## Installation

To use the Fireblocks SDK, follow these steps:

### pip install

If the python package is hosted on a repository, you can install directly using:

```sh
pip install fireblocks
```

Then import the package:
```python
import fireblocks
```

### Setuptools

Install via [Setuptools](http://pypi.python.org/pypi/setuptools).

```sh
python setup.py install --user
```
(or `sudo python setup.py install` to install the package for all users)

Then import the package:
```python
import fireblocks
```

## Usage

Please follow the [installation procedure](#installation) first.

### Initializing the SDK
You can initialize the Fireblocks SDK in two ways, either by setting environment variables or providing the parameters directly:

<p><strong>Using Environment Variables</strong><br>
You can initialize the SDK using environment variables from your .env file or by setting them programmatically:</p>

use bash commands to set environment variables:
```bash
export FIREBLOCKS_BASE_PATH="https://sandbox-api.fireblocks.io/v1"
export FIREBLOCKS_API_KEY="my-api-key"
export FIREBLOCKS_SECRET_KEY="my-secret-key"
```

```python
from fireblocks.client import Fireblocks

# Enter a context with an instance of the API client
with Fireblocks() as fireblocks:
    pass
```

<p><strong>Providing Local Variables</strong><br>

```python
from fireblocks.client import Fireblocks
from fireblocks.client_configuration import ClientConfiguration
from fireblocks.base_path import BasePath


# load the secret key content from a file
with open('your_secret_key_file_path', 'r') as file:
    secret_key_value = file.read()

# build the configuration
configuration = ClientConfiguration(
        api_key="your_api_key",
        secret_key=secret_key_value,
        base_path=BasePath.Sandbox, # or set it directly to a string "https://sandbox-api.fireblocks.io/v1"
)

# Enter a context with an instance of the API client
with Fireblocks(configuration) as fireblocks:
    pass
```

### Basic Api Examples
<p><strong>Creating a Vault Account</strong><br>
    To create a new vault account, you can use the following function:</p>

```python
from fireblocks.client import Fireblocks
from fireblocks.client_configuration import ClientConfiguration
from fireblocks.base_path import BasePath
from fireblocks.models.create_vault_account_request import CreateVaultAccountRequest
from pprint import pprint

# load the secret key content from a file
with open('your_secret_key_file_path', 'r') as file:
    secret_key_value = file.read()

# build the configuration
configuration = ClientConfiguration(
        api_key="your_api_key",
        secret_key=secret_key_value,
        base_path=BasePath.Sandbox, # or set it directly to a string "https://sandbox-api.fireblocks.io/v1"
)

# Enter a context with an instance of the API client
with Fireblocks(configuration) as fireblocks:
    create_vault_account_request: CreateVaultAccountRequest = CreateVaultAccountRequest(
                                    name='My First Vault Account',
                                    hidden_on_ui=False,
                                    auto_fuel=False
                                    )
    try:
        # Create a new vault account
        future = fireblocks.vaults.create_vault_account(create_vault_account_request=create_vault_account_request)
        api_response = future.result()  # Wait for the response
        print("The response of VaultsApi->create_vault_account:\n")
        pprint(api_response)
        # to print just the data:                pprint(api_response.data)
        # to print just the data in json format: pprint(api_response.data.to_json())
    except Exception as e:
        print("Exception when calling VaultsApi->create_vault_account: %s\n" % e)

```


<p><strong>Retrieving Vault Accounts</strong><br>
    To get a list of vault accounts, you can use the following function:</p>

```python
from fireblocks.client import Fireblocks
from fireblocks.client_configuration import ClientConfiguration
from fireblocks.base_path import BasePath
from pprint import pprint

# load the secret key content from a file
with open('your_secret_key_file_path', 'r') as file:
    secret_key_value = file.read()

# build the configuration
configuration = ClientConfiguration(
        api_key="your_api_key",
        secret_key=secret_key_value,
        base_path=BasePath.Sandbox, # or set it directly to a string "https://sandbox-api.fireblocks.io/v1"
)

# Enter a context with an instance of the API client
with Fireblocks(configuration) as fireblocks:
    try:
        # List vault accounts (Paginated)
        future = fireblocks.vaults.get_paged_vault_accounts()
        api_response = future.result()  # Wait for the response
        print("The response of VaultsApi->get_paged_vault_accounts:\n")
        pprint(api_response)
        # to print just the data:                pprint(api_response.data)
        # to print just the data in json format: pprint(api_response.data.to_json())
    except Exception as e:
        print("Exception when calling VaultsApi->get_paged_vault_accounts: %s\n" % e)
```

<p><strong>Creating a Transaction</strong><br>
    To make a transaction between vault accounts, you can use the following function:</p>

```python
from fireblocks.client import Fireblocks
from fireblocks.client_configuration import ClientConfiguration
from fireblocks.base_path import BasePath
from fireblocks.models.transaction_request import TransactionRequest
from fireblocks.models.destination_transfer_peer_path import DestinationTransferPeerPath
from fireblocks.models.source_transfer_peer_path import SourceTransferPeerPath
from fireblocks.models.transfer_peer_path_type import TransferPeerPathType
from fireblocks.models.transaction_request_amount import TransactionRequestAmount
from pprint import pprint

# load the secret key content from a file
with open('your_secret_key_file_path', 'r') as file:
    secret_key_value = file.read()

# build the configuration
configuration = ClientConfiguration(
        api_key="your_api_key",
        secret_key=secret_key_value,
        base_path=BasePath.Sandbox, # or set it directly to a string "https://sandbox-api.fireblocks.io/v1"
)

# Enter a context with an instance of the API client
with Fireblocks(configuration) as fireblocks:
    transaction_request: TransactionRequest = TransactionRequest(
        asset_id="ETH",
        amount=TransactionRequestAmount("0.1"),
        source=SourceTransferPeerPath(
            type=TransferPeerPathType.VAULT_ACCOUNT,
            id="0"
        ),
        destination=DestinationTransferPeerPath(
            type=TransferPeerPathType.VAULT_ACCOUNT,
            id="1"
        ),
        note="Your first transaction!"
    )
    # or you can use JSON approach:
    #
    # transaction_request: TransactionRequest = TransactionRequest.from_json(
    #     '{"note": "Your first transaction!", '
    #     '"assetId": "ETH", '
    #     '"source": {"type": "VAULT_ACCOUNT", "id": "0"}, '
    #     '"destination": {"type": "VAULT_ACCOUNT", "id": "1"}, '
    #     '"amount": "0.1"}'
    # )
    try:
        # Create a new transaction
        future = fireblocks.transactions.create_transaction(transaction_request=transaction_request)
        api_response = future.result()  # Wait for the response
        print("The response of TransactionsApi->create_transaction:\n")
        pprint(api_response)
        # to print just the data:                pprint(api_response.data)
        # to print just the data in json format: pprint(api_response.data.to_json())
    except Exception as e:
        print("Exception when calling TransactionsApi->create_transaction: %s\n" % e)
```

## Documentation for API Endpoints

All URIs are relative to https://developers.fireblocks.com/reference/

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*ApiUserApi* | [**create_api_user**](docs/ApiUserApi.md#create_api_user) | **POST** /management/api_users | Create Api user
*ApiUserApi* | [**get_api_users**](docs/ApiUserApi.md#get_api_users) | **GET** /management/api_users | Get Api users
*AssetsApi* | [**create_assets_bulk**](docs/AssetsApi.md#create_assets_bulk) | **POST** /vault/assets/bulk | Bulk creation of wallets
*AuditLogsApi* | [**get_audit_logs**](docs/AuditLogsApi.md#get_audit_logs) | **GET** /management/audit_logs | Get audit logs
*BlockchainsAssetsApi* | [**get_asset**](docs/BlockchainsAssetsApi.md#get_asset) | **GET** /assets/{id} | Get an asset
*BlockchainsAssetsApi* | [**get_blockchain**](docs/BlockchainsAssetsApi.md#get_blockchain) | **GET** /blockchains/{id} | Get an blockchain
*BlockchainsAssetsApi* | [**get_supported_assets**](docs/BlockchainsAssetsApi.md#get_supported_assets) | **GET** /supported_assets | List all asset types supported by Fireblocks - legacy endpoint
*BlockchainsAssetsApi* | [**list_assets**](docs/BlockchainsAssetsApi.md#list_assets) | **GET** /assets | List assets
*BlockchainsAssetsApi* | [**list_blockchains**](docs/BlockchainsAssetsApi.md#list_blockchains) | **GET** /blockchains | List blockchains
*BlockchainsAssetsApi* | [**register_new_asset**](docs/BlockchainsAssetsApi.md#register_new_asset) | **POST** /assets | Register an asset
*BlockchainsAssetsApi* | [**set_asset_price**](docs/BlockchainsAssetsApi.md#set_asset_price) | **POST** /assets/prices/{id} | Set asset price
*BlockchainsAssetsApi* | [**update_asset_user_metadata**](docs/BlockchainsAssetsApi.md#update_asset_user_metadata) | **PATCH** /assets/{id} | Update the user’s metadata for an asset
*ComplianceApi* | [**get_aml_post_screening_policy**](docs/ComplianceApi.md#get_aml_post_screening_policy) | **GET** /screening/aml/post_screening_policy | AML - View Post-Screening Policy
*ComplianceApi* | [**get_aml_screening_policy**](docs/ComplianceApi.md#get_aml_screening_policy) | **GET** /screening/aml/screening_policy | AML - View Screening Policy
*ComplianceApi* | [**get_post_screening_policy**](docs/ComplianceApi.md#get_post_screening_policy) | **GET** /screening/travel_rule/post_screening_policy | Travel Rule - View Post-Screening Policy
*ComplianceApi* | [**get_screening_full_details**](docs/ComplianceApi.md#get_screening_full_details) | **GET** /screening/transaction/{txId} | Provides all the compliance details for the given screened transaction.
*ComplianceApi* | [**get_screening_policy**](docs/ComplianceApi.md#get_screening_policy) | **GET** /screening/travel_rule/screening_policy | Travel Rule - View Screening Policy
*ComplianceApi* | [**retry_rejected_transaction_bypass_screening_checks**](docs/ComplianceApi.md#retry_rejected_transaction_bypass_screening_checks) | **POST** /screening/transaction/{txId}/bypass_screening_policy | Calling the \&quot;Bypass Screening Policy\&quot; API endpoint triggers a new transaction, with the API user as the initiator, bypassing the screening policy check
*ComplianceApi* | [**set_aml_verdict**](docs/ComplianceApi.md#set_aml_verdict) | **POST** /screening/aml/verdict/manual | Set AML Verdict for Manual Screening Verdict.
*ComplianceApi* | [**update_aml_screening_configuration**](docs/ComplianceApi.md#update_aml_screening_configuration) | **PUT** /screening/aml/policy_configuration | Update AML Configuration
*ComplianceApi* | [**update_screening_configuration**](docs/ComplianceApi.md#update_screening_configuration) | **PUT** /screening/configurations | Tenant - Screening Configuration
*ComplianceApi* | [**update_travel_rule_config**](docs/ComplianceApi.md#update_travel_rule_config) | **PUT** /screening/travel_rule/policy_configuration | Update Travel Rule Configuration
*ComplianceScreeningConfigurationApi* | [**get_aml_screening_configuration**](docs/ComplianceScreeningConfigurationApi.md#get_aml_screening_configuration) | **GET** /screening/aml/policy_configuration | Get AML Screening Policy Configuration
*ComplianceScreeningConfigurationApi* | [**get_screening_configuration**](docs/ComplianceScreeningConfigurationApi.md#get_screening_configuration) | **GET** /screening/travel_rule/policy_configuration | Get Travel Rule Screening Policy Configuration
*ConnectedAccountsBetaApi* | [**get_connected_account**](docs/ConnectedAccountsBetaApi.md#get_connected_account) | **GET** /connected_accounts/{accountId} | Get connected account
*ConnectedAccountsBetaApi* | [**get_connected_account_balances**](docs/ConnectedAccountsBetaApi.md#get_connected_account_balances) | **GET** /connected_accounts/{accountId}/balances | Get balances for an account
*ConnectedAccountsBetaApi* | [**get_connected_account_rates**](docs/ConnectedAccountsBetaApi.md#get_connected_account_rates) | **GET** /connected_accounts/{accountId}/rates | Get exchange rates for an account
*ConnectedAccountsBetaApi* | [**get_connected_account_trading_pairs**](docs/ConnectedAccountsBetaApi.md#get_connected_account_trading_pairs) | **GET** /connected_accounts/{accountId}/manifest/capabilities/trading/pairs | Get supported trading pairs for an account
*ConnectedAccountsBetaApi* | [**get_connected_accounts**](docs/ConnectedAccountsBetaApi.md#get_connected_accounts) | **GET** /connected_accounts | Get connected accounts
*ConsoleUserApi* | [**create_console_user**](docs/ConsoleUserApi.md#create_console_user) | **POST** /management/users | Create console user
*ConsoleUserApi* | [**get_console_users**](docs/ConsoleUserApi.md#get_console_users) | **GET** /management/users | Get console users
*ContractInteractionsApi* | [**decode_contract_data**](docs/ContractInteractionsApi.md#decode_contract_data) | **POST** /contract_interactions/base_asset_id/{baseAssetId}/contract_address/{contractAddress}/decode | Decode a function call data, error, or event log
*ContractInteractionsApi* | [**get_deployed_contract_abi**](docs/ContractInteractionsApi.md#get_deployed_contract_abi) | **GET** /contract_interactions/base_asset_id/{baseAssetId}/contract_address/{contractAddress}/functions | Return deployed contract&#39;s ABI
*ContractInteractionsApi* | [**get_transaction_receipt**](docs/ContractInteractionsApi.md#get_transaction_receipt) | **GET** /contract_interactions/base_asset_id/{baseAssetId}/tx_hash/{txHash}/receipt | Get transaction receipt
*ContractInteractionsApi* | [**read_call_function**](docs/ContractInteractionsApi.md#read_call_function) | **POST** /contract_interactions/base_asset_id/{baseAssetId}/contract_address/{contractAddress}/functions/read | Call a read function on a deployed contract
*ContractInteractionsApi* | [**write_call_function**](docs/ContractInteractionsApi.md#write_call_function) | **POST** /contract_interactions/base_asset_id/{baseAssetId}/contract_address/{contractAddress}/functions/write | Call a write function on a deployed contract
*ContractTemplatesApi* | [**delete_contract_template_by_id**](docs/ContractTemplatesApi.md#delete_contract_template_by_id) | **DELETE** /tokenization/templates/{contractTemplateId} | Delete a contract template by id
*ContractTemplatesApi* | [**deploy_contract**](docs/ContractTemplatesApi.md#deploy_contract) | **POST** /tokenization/templates/{contractTemplateId}/deploy | Deploy contract
*ContractTemplatesApi* | [**get_constructor_by_contract_template_id**](docs/ContractTemplatesApi.md#get_constructor_by_contract_template_id) | **GET** /tokenization/templates/{contractTemplateId}/constructor | Return contract template&#39;s constructor
*ContractTemplatesApi* | [**get_contract_template_by_id**](docs/ContractTemplatesApi.md#get_contract_template_by_id) | **GET** /tokenization/templates/{contractTemplateId} | Return contract template by id
*ContractTemplatesApi* | [**get_contract_templates**](docs/ContractTemplatesApi.md#get_contract_templates) | **GET** /tokenization/templates | List all contract templates
*ContractTemplatesApi* | [**get_function_abi_by_contract_template_id**](docs/ContractTemplatesApi.md#get_function_abi_by_contract_template_id) | **GET** /tokenization/templates/{contractTemplateId}/function | Return contract template&#39;s function
*ContractTemplatesApi* | [**upload_contract_template**](docs/ContractTemplatesApi.md#upload_contract_template) | **POST** /tokenization/templates | Upload contract template
*ContractsApi* | [**add_contract_asset**](docs/ContractsApi.md#add_contract_asset) | **POST** /contracts/{contractId}/{assetId} | Add an asset to a contract
*ContractsApi* | [**create_contract**](docs/ContractsApi.md#create_contract) | **POST** /contracts | Create a contract
*ContractsApi* | [**delete_contract**](docs/ContractsApi.md#delete_contract) | **DELETE** /contracts/{contractId} | Delete a contract
*ContractsApi* | [**delete_contract_asset**](docs/ContractsApi.md#delete_contract_asset) | **DELETE** /contracts/{contractId}/{assetId} | Delete a contract asset
*ContractsApi* | [**get_contract**](docs/ContractsApi.md#get_contract) | **GET** /contracts/{contractId} | Find a specific contract
*ContractsApi* | [**get_contract_asset**](docs/ContractsApi.md#get_contract_asset) | **GET** /contracts/{contractId}/{assetId} | Find a contract asset
*ContractsApi* | [**get_contracts**](docs/ContractsApi.md#get_contracts) | **GET** /contracts | List contracts
*CosignersBetaApi* | [**add_cosigner**](docs/CosignersBetaApi.md#add_cosigner) | **POST** /cosigners | Add cosigner
*CosignersBetaApi* | [**get_api_key**](docs/CosignersBetaApi.md#get_api_key) | **GET** /cosigners/{cosignerId}/api_keys/{apiKeyId} | Get API key
*CosignersBetaApi* | [**get_api_keys**](docs/CosignersBetaApi.md#get_api_keys) | **GET** /cosigners/{cosignerId}/api_keys | Get all API keys
*CosignersBetaApi* | [**get_cosigner**](docs/CosignersBetaApi.md#get_cosigner) | **GET** /cosigners/{cosignerId} | Get cosigner
*CosignersBetaApi* | [**get_cosigners**](docs/CosignersBetaApi.md#get_cosigners) | **GET** /cosigners | Get all cosigners
*CosignersBetaApi* | [**get_request_status**](docs/CosignersBetaApi.md#get_request_status) | **GET** /cosigners/{cosignerId}/api_keys/{apiKeyId}/{requestId} | Get request status
*CosignersBetaApi* | [**pair_api_key**](docs/CosignersBetaApi.md#pair_api_key) | **PUT** /cosigners/{cosignerId}/api_keys/{apiKeyId} | Pair API key
*CosignersBetaApi* | [**rename_cosigner**](docs/CosignersBetaApi.md#rename_cosigner) | **PATCH** /cosigners/{cosignerId} | Rename cosigner
*CosignersBetaApi* | [**unpair_api_key**](docs/CosignersBetaApi.md#unpair_api_key) | **DELETE** /cosigners/{cosignerId}/api_keys/{apiKeyId} | Unpair API key
*CosignersBetaApi* | [**update_callback_handler**](docs/CosignersBetaApi.md#update_callback_handler) | **PATCH** /cosigners/{cosignerId}/api_keys/{apiKeyId} | Update API key callback handler
*DeployedContractsApi* | [**add_contract_abi**](docs/DeployedContractsApi.md#add_contract_abi) | **POST** /tokenization/contracts/abi | Save contract ABI
*DeployedContractsApi* | [**fetch_contract_abi**](docs/DeployedContractsApi.md#fetch_contract_abi) | **POST** /tokenization/contracts/fetch_abi | Fetch the contract ABI
*DeployedContractsApi* | [**get_deployed_contract_by_address**](docs/DeployedContractsApi.md#get_deployed_contract_by_address) | **GET** /tokenization/contracts/{assetId}/{contractAddress} | Return deployed contract data
*DeployedContractsApi* | [**get_deployed_contract_by_id**](docs/DeployedContractsApi.md#get_deployed_contract_by_id) | **GET** /tokenization/contracts/{id} | Return deployed contract data by id
*DeployedContractsApi* | [**get_deployed_contracts**](docs/DeployedContractsApi.md#get_deployed_contracts) | **GET** /tokenization/contracts | List deployed contracts data
*EmbeddedWalletsApi* | [**add_embedded_wallet_asset**](docs/EmbeddedWalletsApi.md#add_embedded_wallet_asset) | **POST** /ncw/wallets/{walletId}/accounts/{accountId}/assets/{assetId} | Add asset to account
*EmbeddedWalletsApi* | [**create_embedded_wallet**](docs/EmbeddedWalletsApi.md#create_embedded_wallet) | **POST** /ncw/wallets | Create a new wallet
*EmbeddedWalletsApi* | [**create_embedded_wallet_account**](docs/EmbeddedWalletsApi.md#create_embedded_wallet_account) | **POST** /ncw/wallets/{walletId}/accounts | Create a new account
*EmbeddedWalletsApi* | [**get_embedded_wallet**](docs/EmbeddedWalletsApi.md#get_embedded_wallet) | **GET** /ncw/wallets/{walletId} | Get a wallet
*EmbeddedWalletsApi* | [**get_embedded_wallet_account**](docs/EmbeddedWalletsApi.md#get_embedded_wallet_account) | **GET** /ncw/wallets/{walletId}/accounts/{accountId} | Get a account
*EmbeddedWalletsApi* | [**get_embedded_wallet_addresses**](docs/EmbeddedWalletsApi.md#get_embedded_wallet_addresses) | **GET** /ncw/wallets/{walletId}/accounts/{accountId}/assets/{assetId}/addresses | Retrieve asset addresses
*EmbeddedWalletsApi* | [**get_embedded_wallet_asset**](docs/EmbeddedWalletsApi.md#get_embedded_wallet_asset) | **GET** /ncw/wallets/{walletId}/accounts/{accountId}/assets/{assetId} | Retrieve asset
*EmbeddedWalletsApi* | [**get_embedded_wallet_asset_balance**](docs/EmbeddedWalletsApi.md#get_embedded_wallet_asset_balance) | **GET** /ncw/wallets/{walletId}/accounts/{accountId}/assets/{assetId}/balance | Retrieve asset balance
*EmbeddedWalletsApi* | [**get_embedded_wallet_device**](docs/EmbeddedWalletsApi.md#get_embedded_wallet_device) | **GET** /ncw/wallets/{walletId}/devices/{deviceId} | Get Embedded Wallet Device
*EmbeddedWalletsApi* | [**get_embedded_wallet_device_setup_state**](docs/EmbeddedWalletsApi.md#get_embedded_wallet_device_setup_state) | **GET** /ncw/wallets/{walletId}/devices/{deviceId}/setup_status | Get device key setup state
*EmbeddedWalletsApi* | [**get_embedded_wallet_latest_backup**](docs/EmbeddedWalletsApi.md#get_embedded_wallet_latest_backup) | **GET** /ncw/wallets/{walletId}/backup/latest | Get wallet Latest Backup details
*EmbeddedWalletsApi* | [**get_embedded_wallet_public_key_info_for_address**](docs/EmbeddedWalletsApi.md#get_embedded_wallet_public_key_info_for_address) | **GET** /ncw/wallets/{walletId}/accounts/{accountId}/assets/{assetId}/{change}/{addressIndex}/public_key_info | Get the public key of an asset
*EmbeddedWalletsApi* | [**get_embedded_wallet_supported_assets**](docs/EmbeddedWalletsApi.md#get_embedded_wallet_supported_assets) | **GET** /ncw/wallets/supported_assets | Retrieve supported assets
*EmbeddedWalletsApi* | [**get_embedded_wallets**](docs/EmbeddedWalletsApi.md#get_embedded_wallets) | **GET** /ncw/wallets | List wallets
*EmbeddedWalletsApi* | [**get_public_key_info_ncw**](docs/EmbeddedWalletsApi.md#get_public_key_info_ncw) | **GET** /ncw/wallets/{walletId}/public_key_info | Get the public key for a derivation path
*EmbeddedWalletsApi* | [**refresh_embedded_wallet_asset_balance**](docs/EmbeddedWalletsApi.md#refresh_embedded_wallet_asset_balance) | **PUT** /ncw/wallets/{walletId}/accounts/{accountId}/assets/{assetId}/balance | Refresh asset balance
*ExchangeAccountsApi* | [**add_exchange_account**](docs/ExchangeAccountsApi.md#add_exchange_account) | **POST** /exchange_accounts | Add an exchange account
*ExchangeAccountsApi* | [**convert_assets**](docs/ExchangeAccountsApi.md#convert_assets) | **POST** /exchange_accounts/{exchangeAccountId}/convert | Convert exchange account funds from the source asset to the destination asset.
*ExchangeAccountsApi* | [**get_exchange_account**](docs/ExchangeAccountsApi.md#get_exchange_account) | **GET** /exchange_accounts/{exchangeAccountId} | Find a specific exchange account
*ExchangeAccountsApi* | [**get_exchange_account_asset**](docs/ExchangeAccountsApi.md#get_exchange_account_asset) | **GET** /exchange_accounts/{exchangeAccountId}/{assetId} | Find an asset for an exchange account
*ExchangeAccountsApi* | [**get_exchange_accounts_credentials_public_key**](docs/ExchangeAccountsApi.md#get_exchange_accounts_credentials_public_key) | **GET** /exchange_accounts/credentials_public_key | Get public key to encrypt exchange credentials
*ExchangeAccountsApi* | [**get_paged_exchange_accounts**](docs/ExchangeAccountsApi.md#get_paged_exchange_accounts) | **GET** /exchange_accounts/paged | Pagination list exchange accounts
*ExchangeAccountsApi* | [**internal_transfer**](docs/ExchangeAccountsApi.md#internal_transfer) | **POST** /exchange_accounts/{exchangeAccountId}/internal_transfer | Internal transfer for exchange accounts
*ExternalWalletsApi* | [**add_asset_to_external_wallet**](docs/ExternalWalletsApi.md#add_asset_to_external_wallet) | **POST** /external_wallets/{walletId}/{assetId} | Add an asset to an external wallet.
*ExternalWalletsApi* | [**create_external_wallet**](docs/ExternalWalletsApi.md#create_external_wallet) | **POST** /external_wallets | Create an external wallet
*ExternalWalletsApi* | [**delete_external_wallet**](docs/ExternalWalletsApi.md#delete_external_wallet) | **DELETE** /external_wallets/{walletId} | Delete an external wallet
*ExternalWalletsApi* | [**get_external_wallet**](docs/ExternalWalletsApi.md#get_external_wallet) | **GET** /external_wallets/{walletId} | Find an external wallet
*ExternalWalletsApi* | [**get_external_wallet_asset**](docs/ExternalWalletsApi.md#get_external_wallet_asset) | **GET** /external_wallets/{walletId}/{assetId} | Get an asset from an external wallet
*ExternalWalletsApi* | [**get_external_wallets**](docs/ExternalWalletsApi.md#get_external_wallets) | **GET** /external_wallets | List external wallets
*ExternalWalletsApi* | [**remove_asset_from_external_wallet**](docs/ExternalWalletsApi.md#remove_asset_from_external_wallet) | **DELETE** /external_wallets/{walletId}/{assetId} | Delete an asset from an external wallet
*ExternalWalletsApi* | [**set_external_wallet_customer_ref_id**](docs/ExternalWalletsApi.md#set_external_wallet_customer_ref_id) | **POST** /external_wallets/{walletId}/set_customer_ref_id | Set an AML customer reference ID for an external wallet
*FiatAccountsApi* | [**deposit_funds_from_linked_dda**](docs/FiatAccountsApi.md#deposit_funds_from_linked_dda) | **POST** /fiat_accounts/{accountId}/deposit_from_linked_dda | Deposit funds from DDA
*FiatAccountsApi* | [**get_fiat_account**](docs/FiatAccountsApi.md#get_fiat_account) | **GET** /fiat_accounts/{accountId} | Find a specific fiat account
*FiatAccountsApi* | [**get_fiat_accounts**](docs/FiatAccountsApi.md#get_fiat_accounts) | **GET** /fiat_accounts | List fiat accounts
*FiatAccountsApi* | [**redeem_funds_to_linked_dda**](docs/FiatAccountsApi.md#redeem_funds_to_linked_dda) | **POST** /fiat_accounts/{accountId}/redeem_to_linked_dda | Redeem funds to DDA
*GasStationsApi* | [**get_gas_station_by_asset_id**](docs/GasStationsApi.md#get_gas_station_by_asset_id) | **GET** /gas_station/{assetId} | Get gas station settings by asset
*GasStationsApi* | [**get_gas_station_info**](docs/GasStationsApi.md#get_gas_station_info) | **GET** /gas_station | Get gas station settings
*GasStationsApi* | [**update_gas_station_configuration**](docs/GasStationsApi.md#update_gas_station_configuration) | **PUT** /gas_station/configuration | Edit gas station settings
*GasStationsApi* | [**update_gas_station_configuration_by_asset_id**](docs/GasStationsApi.md#update_gas_station_configuration_by_asset_id) | **PUT** /gas_station/configuration/{assetId} | Edit gas station settings for an asset
*InternalWalletsApi* | [**create_internal_wallet**](docs/InternalWalletsApi.md#create_internal_wallet) | **POST** /internal_wallets | Create an internal wallet
*InternalWalletsApi* | [**create_internal_wallet_asset**](docs/InternalWalletsApi.md#create_internal_wallet_asset) | **POST** /internal_wallets/{walletId}/{assetId} | Add an asset to an internal wallet
*InternalWalletsApi* | [**delete_internal_wallet**](docs/InternalWalletsApi.md#delete_internal_wallet) | **DELETE** /internal_wallets/{walletId} | Delete an internal wallet
*InternalWalletsApi* | [**delete_internal_wallet_asset**](docs/InternalWalletsApi.md#delete_internal_wallet_asset) | **DELETE** /internal_wallets/{walletId}/{assetId} | Delete a whitelisted address
*InternalWalletsApi* | [**get_internal_wallet**](docs/InternalWalletsApi.md#get_internal_wallet) | **GET** /internal_wallets/{walletId} | Get an asset from an internal wallet
*InternalWalletsApi* | [**get_internal_wallet_asset**](docs/InternalWalletsApi.md#get_internal_wallet_asset) | **GET** /internal_wallets/{walletId}/{assetId} | Get an asset from an internal wallet
*InternalWalletsApi* | [**get_internal_wallet_assets_paginated**](docs/InternalWalletsApi.md#get_internal_wallet_assets_paginated) | **GET** /internal_wallets/{walletId}/assets | List assets in an internal wallet (Paginated)
*InternalWalletsApi* | [**get_internal_wallets**](docs/InternalWalletsApi.md#get_internal_wallets) | **GET** /internal_wallets | List internal wallets
*InternalWalletsApi* | [**set_customer_ref_id_for_internal_wallet**](docs/InternalWalletsApi.md#set_customer_ref_id_for_internal_wallet) | **POST** /internal_wallets/{walletId}/set_customer_ref_id | Set an AML/KYT customer reference ID for an internal wallet
*JobManagementApi* | [**cancel_job**](docs/JobManagementApi.md#cancel_job) | **POST** /batch/{jobId}/cancel | Cancel a running job
*JobManagementApi* | [**continue_job**](docs/JobManagementApi.md#continue_job) | **POST** /batch/{jobId}/continue | Continue a paused job
*JobManagementApi* | [**get_job**](docs/JobManagementApi.md#get_job) | **GET** /batch/{jobId} | Get job details
*JobManagementApi* | [**get_job_tasks**](docs/JobManagementApi.md#get_job_tasks) | **GET** /batch/{jobId}/tasks | Return a list of tasks for given job
*JobManagementApi* | [**get_jobs**](docs/JobManagementApi.md#get_jobs) | **GET** /batch/jobs | Return a list of jobs belonging to tenant
*JobManagementApi* | [**pause_job**](docs/JobManagementApi.md#pause_job) | **POST** /batch/{jobId}/pause | Pause a job
*KeyLinkBetaApi* | [**create_signing_key**](docs/KeyLinkBetaApi.md#create_signing_key) | **POST** /key_link/signing_keys | Add a new signing key
*KeyLinkBetaApi* | [**create_validation_key**](docs/KeyLinkBetaApi.md#create_validation_key) | **POST** /key_link/validation_keys | Add a new validation key
*KeyLinkBetaApi* | [**disable_validation_key**](docs/KeyLinkBetaApi.md#disable_validation_key) | **PATCH** /key_link/validation_keys/{keyId} | Disables a validation key
*KeyLinkBetaApi* | [**get_signing_key**](docs/KeyLinkBetaApi.md#get_signing_key) | **GET** /key_link/signing_keys/{keyId} | Get a signing key by &#x60;keyId&#x60;
*KeyLinkBetaApi* | [**get_signing_keys_list**](docs/KeyLinkBetaApi.md#get_signing_keys_list) | **GET** /key_link/signing_keys | Get list of signing keys
*KeyLinkBetaApi* | [**get_validation_key**](docs/KeyLinkBetaApi.md#get_validation_key) | **GET** /key_link/validation_keys/{keyId} | Get a validation key by &#x60;keyId&#x60;
*KeyLinkBetaApi* | [**get_validation_keys_list**](docs/KeyLinkBetaApi.md#get_validation_keys_list) | **GET** /key_link/validation_keys | Get list of registered validation keys
*KeyLinkBetaApi* | [**set_agent_id**](docs/KeyLinkBetaApi.md#set_agent_id) | **PATCH** /key_link/signing_keys/{keyId}/agent_user_id | Set agent user id that can sign with the signing key identified by the Fireblocks provided &#x60;keyId&#x60;
*KeyLinkBetaApi* | [**update_signing_key**](docs/KeyLinkBetaApi.md#update_signing_key) | **PATCH** /key_link/signing_keys/{keyId} | Modify the signing by Fireblocks provided &#x60;keyId&#x60;
*KeysBetaApi* | [**get_mpc_keys_list**](docs/KeysBetaApi.md#get_mpc_keys_list) | **GET** /keys/mpc/list | Get list of mpc keys
*KeysBetaApi* | [**get_mpc_keys_list_by_user**](docs/KeysBetaApi.md#get_mpc_keys_list_by_user) | **GET** /keys/mpc/list/{userId} | Get list of mpc keys by &#x60;userId&#x60;
*NFTsApi* | [**get_nft**](docs/NFTsApi.md#get_nft) | **GET** /nfts/tokens/{id} | List token data by ID
*NFTsApi* | [**get_nfts**](docs/NFTsApi.md#get_nfts) | **GET** /nfts/tokens | List tokens by IDs
*NFTsApi* | [**get_ownership_tokens**](docs/NFTsApi.md#get_ownership_tokens) | **GET** /nfts/ownership/tokens | List all owned tokens (paginated)
*NFTsApi* | [**list_owned_collections**](docs/NFTsApi.md#list_owned_collections) | **GET** /nfts/ownership/collections | List owned collections (paginated)
*NFTsApi* | [**list_owned_tokens**](docs/NFTsApi.md#list_owned_tokens) | **GET** /nfts/ownership/assets | List all distinct owned tokens (paginated)
*NFTsApi* | [**refresh_nft_metadata**](docs/NFTsApi.md#refresh_nft_metadata) | **PUT** /nfts/tokens/{id} | Refresh token metadata
*NFTsApi* | [**update_ownership_tokens**](docs/NFTsApi.md#update_ownership_tokens) | **PUT** /nfts/ownership/tokens | Refresh vault account tokens
*NFTsApi* | [**update_token_ownership_status**](docs/NFTsApi.md#update_token_ownership_status) | **PUT** /nfts/ownership/tokens/{id}/status | Update token ownership status
*NFTsApi* | [**update_tokens_ownership_spam**](docs/NFTsApi.md#update_tokens_ownership_spam) | **PUT** /nfts/ownership/tokens/spam | Update tokens ownership spam property
*NFTsApi* | [**update_tokens_ownership_status**](docs/NFTsApi.md#update_tokens_ownership_status) | **PUT** /nfts/ownership/tokens/status | Update tokens ownership status
*NetworkConnectionsApi* | [**check_third_party_routing**](docs/NetworkConnectionsApi.md#check_third_party_routing) | **GET** /network_connections/{connectionId}/is_third_party_routing/{assetType} | Retrieve third-party network routing validation by asset type.
*NetworkConnectionsApi* | [**create_network_connection**](docs/NetworkConnectionsApi.md#create_network_connection) | **POST** /network_connections | Creates a new network connection
*NetworkConnectionsApi* | [**create_network_id**](docs/NetworkConnectionsApi.md#create_network_id) | **POST** /network_ids | Creates a new Network ID
*NetworkConnectionsApi* | [**delete_network_connection**](docs/NetworkConnectionsApi.md#delete_network_connection) | **DELETE** /network_connections/{connectionId} | Deletes a network connection by ID
*NetworkConnectionsApi* | [**delete_network_id**](docs/NetworkConnectionsApi.md#delete_network_id) | **DELETE** /network_ids/{networkId} | Deletes specific network ID.
*NetworkConnectionsApi* | [**get_network**](docs/NetworkConnectionsApi.md#get_network) | **GET** /network_connections/{connectionId} | Get a network connection
*NetworkConnectionsApi* | [**get_network_connections**](docs/NetworkConnectionsApi.md#get_network_connections) | **GET** /network_connections | List network connections
*NetworkConnectionsApi* | [**get_network_id**](docs/NetworkConnectionsApi.md#get_network_id) | **GET** /network_ids/{networkId} | Returns specific network ID.
*NetworkConnectionsApi* | [**get_network_ids**](docs/NetworkConnectionsApi.md#get_network_ids) | **GET** /network_ids | Returns all network IDs, both local IDs and discoverable remote IDs
*NetworkConnectionsApi* | [**get_routing_policy_asset_groups**](docs/NetworkConnectionsApi.md#get_routing_policy_asset_groups) | **GET** /network_ids/routing_policy_asset_groups | Returns all enabled routing policy asset groups
*NetworkConnectionsApi* | [**search_network_ids**](docs/NetworkConnectionsApi.md#search_network_ids) | **GET** /network_ids/search | Search network IDs, both local IDs and discoverable remote IDs
*NetworkConnectionsApi* | [**set_network_id_discoverability**](docs/NetworkConnectionsApi.md#set_network_id_discoverability) | **PATCH** /network_ids/{networkId}/set_discoverability | Update network ID&#39;s discoverability.
*NetworkConnectionsApi* | [**set_network_id_name**](docs/NetworkConnectionsApi.md#set_network_id_name) | **PATCH** /network_ids/{networkId}/set_name | Update network ID&#39;s name.
*NetworkConnectionsApi* | [**set_network_id_routing_policy**](docs/NetworkConnectionsApi.md#set_network_id_routing_policy) | **PATCH** /network_ids/{networkId}/set_routing_policy | Update network id routing policy.
*NetworkConnectionsApi* | [**set_routing_policy**](docs/NetworkConnectionsApi.md#set_routing_policy) | **PATCH** /network_connections/{connectionId}/set_routing_policy | Update network connection routing policy.
*OTABetaApi* | [**get_ota_status**](docs/OTABetaApi.md#get_ota_status) | **GET** /management/ota | Returns current OTA status
*OTABetaApi* | [**set_ota_status**](docs/OTABetaApi.md#set_ota_status) | **PUT** /management/ota | Enable or disable transactions to OTA
*OffExchangesApi* | [**add_off_exchange**](docs/OffExchangesApi.md#add_off_exchange) | **POST** /off_exchange/add | add collateral
*OffExchangesApi* | [**get_off_exchange_collateral_accounts**](docs/OffExchangesApi.md#get_off_exchange_collateral_accounts) | **GET** /off_exchange/collateral_accounts/{mainExchangeAccountId} | Find a specific collateral exchange account
*OffExchangesApi* | [**get_off_exchange_settlement_transactions**](docs/OffExchangesApi.md#get_off_exchange_settlement_transactions) | **GET** /off_exchange/settlements/transactions | get settlements transactions from exchange
*OffExchangesApi* | [**remove_off_exchange**](docs/OffExchangesApi.md#remove_off_exchange) | **POST** /off_exchange/remove | remove collateral
*OffExchangesApi* | [**settle_off_exchange_trades**](docs/OffExchangesApi.md#settle_off_exchange_trades) | **POST** /off_exchange/settlements/trader | create settlement for a trader
*PaymentsPayoutApi* | [**create_payout**](docs/PaymentsPayoutApi.md#create_payout) | **POST** /payments/payout | Create a payout instruction set
*PaymentsPayoutApi* | [**execute_payout_action**](docs/PaymentsPayoutApi.md#execute_payout_action) | **POST** /payments/payout/{payoutId}/actions/execute | Execute a payout instruction set
*PaymentsPayoutApi* | [**get_payout**](docs/PaymentsPayoutApi.md#get_payout) | **GET** /payments/payout/{payoutId} | Get the status of a payout instruction set
*PolicyEditorV2BetaApi* | [**get_active_policy**](docs/PolicyEditorV2BetaApi.md#get_active_policy) | **GET** /policy/active_policy | Get the active policy and its validation by policy type
*PolicyEditorV2BetaApi* | [**get_draft**](docs/PolicyEditorV2BetaApi.md#get_draft) | **GET** /policy/draft | Get the active draft by policy type
*PolicyEditorV2BetaApi* | [**publish_draft**](docs/PolicyEditorV2BetaApi.md#publish_draft) | **POST** /policy/draft | Send publish request for a certain draft id
*PolicyEditorV2BetaApi* | [**update_draft**](docs/PolicyEditorV2BetaApi.md#update_draft) | **PUT** /policy/draft | Update the draft with a new set of rules by policy types
*PolicyEditorBetaApi* | [**get_active_policy_legacy**](docs/PolicyEditorBetaApi.md#get_active_policy_legacy) | **GET** /tap/active_policy | Get the active policy and its validation
*PolicyEditorBetaApi* | [**get_draft_legacy**](docs/PolicyEditorBetaApi.md#get_draft_legacy) | **GET** /tap/draft | Get the active draft
*PolicyEditorBetaApi* | [**publish_draft_legacy**](docs/PolicyEditorBetaApi.md#publish_draft_legacy) | **POST** /tap/draft | Send publish request for a certain draft id
*PolicyEditorBetaApi* | [**publish_policy_rules**](docs/PolicyEditorBetaApi.md#publish_policy_rules) | **POST** /tap/publish | Send publish request for a set of policy rules
*PolicyEditorBetaApi* | [**update_draft_legacy**](docs/PolicyEditorBetaApi.md#update_draft_legacy) | **PUT** /tap/draft | Update the draft with a new set of rules
*ResetDeviceApi* | [**reset_device**](docs/ResetDeviceApi.md#reset_device) | **POST** /management/users/{id}/reset_device | Resets device
*SmartTransferApi* | [**approve_dv_p_ticket_term**](docs/SmartTransferApi.md#approve_dv_p_ticket_term) | **PUT** /smart_transfers/{ticketId}/terms/{termId}/dvp/approve | Define funding source and give approve to contract to transfer asset
*SmartTransferApi* | [**cancel_ticket**](docs/SmartTransferApi.md#cancel_ticket) | **PUT** /smart-transfers/{ticketId}/cancel | Cancel Ticket
*SmartTransferApi* | [**create_ticket**](docs/SmartTransferApi.md#create_ticket) | **POST** /smart-transfers | Create Ticket
*SmartTransferApi* | [**create_ticket_term**](docs/SmartTransferApi.md#create_ticket_term) | **POST** /smart-transfers/{ticketId}/terms | Create leg (term)
*SmartTransferApi* | [**find_ticket_by_id**](docs/SmartTransferApi.md#find_ticket_by_id) | **GET** /smart-transfers/{ticketId} | Search Tickets by ID
*SmartTransferApi* | [**find_ticket_term_by_id**](docs/SmartTransferApi.md#find_ticket_term_by_id) | **GET** /smart-transfers/{ticketId}/terms/{termId} | Search ticket by leg (term) ID
*SmartTransferApi* | [**fulfill_ticket**](docs/SmartTransferApi.md#fulfill_ticket) | **PUT** /smart-transfers/{ticketId}/fulfill | Fund ticket manually
*SmartTransferApi* | [**fund_dvp_ticket**](docs/SmartTransferApi.md#fund_dvp_ticket) | **PUT** /smart_transfers/{ticketId}/dvp/fund | Fund dvp ticket
*SmartTransferApi* | [**fund_ticket_term**](docs/SmartTransferApi.md#fund_ticket_term) | **PUT** /smart-transfers/{ticketId}/terms/{termId}/fund | Define funding source
*SmartTransferApi* | [**get_smart_transfer_statistic**](docs/SmartTransferApi.md#get_smart_transfer_statistic) | **GET** /smart_transfers/statistic | Get smart transfers statistic
*SmartTransferApi* | [**get_smart_transfer_user_groups**](docs/SmartTransferApi.md#get_smart_transfer_user_groups) | **GET** /smart-transfers/settings/user-groups | Get user group
*SmartTransferApi* | [**manually_fund_ticket_term**](docs/SmartTransferApi.md#manually_fund_ticket_term) | **PUT** /smart-transfers/{ticketId}/terms/{termId}/manually-fund | Manually add term transaction
*SmartTransferApi* | [**remove_ticket_term**](docs/SmartTransferApi.md#remove_ticket_term) | **DELETE** /smart-transfers/{ticketId}/terms/{termId} | Delete ticket leg (term)
*SmartTransferApi* | [**search_tickets**](docs/SmartTransferApi.md#search_tickets) | **GET** /smart-transfers | Find Ticket
*SmartTransferApi* | [**set_external_ref_id**](docs/SmartTransferApi.md#set_external_ref_id) | **PUT** /smart-transfers/{ticketId}/external-id | Add external ref. ID
*SmartTransferApi* | [**set_ticket_expiration**](docs/SmartTransferApi.md#set_ticket_expiration) | **PUT** /smart-transfers/{ticketId}/expires-in | Set expiration
*SmartTransferApi* | [**set_user_groups**](docs/SmartTransferApi.md#set_user_groups) | **POST** /smart-transfers/settings/user-groups | Set user group
*SmartTransferApi* | [**submit_ticket**](docs/SmartTransferApi.md#submit_ticket) | **PUT** /smart-transfers/{ticketId}/submit | Submit ticket
*SmartTransferApi* | [**update_ticket_term**](docs/SmartTransferApi.md#update_ticket_term) | **PUT** /smart-transfers/{ticketId}/terms/{termId} | Update ticket leg (term)
*StakingApi* | [**approve_terms_of_service_by_provider_id**](docs/StakingApi.md#approve_terms_of_service_by_provider_id) | **POST** /staking/providers/{providerId}/approveTermsOfService | Approve staking terms of service
*StakingApi* | [**claim_rewards**](docs/StakingApi.md#claim_rewards) | **POST** /staking/chains/{chainDescriptor}/claim_rewards | Execute a Claim Rewards operation
*StakingApi* | [**get_all_delegations**](docs/StakingApi.md#get_all_delegations) | **GET** /staking/positions | List staking positions details
*StakingApi* | [**get_chain_info**](docs/StakingApi.md#get_chain_info) | **GET** /staking/chains/{chainDescriptor}/chainInfo | Get chain-specific staking summary
*StakingApi* | [**get_chains**](docs/StakingApi.md#get_chains) | **GET** /staking/chains | List staking supported chains
*StakingApi* | [**get_delegation_by_id**](docs/StakingApi.md#get_delegation_by_id) | **GET** /staking/positions/{id} | Get staking position details
*StakingApi* | [**get_providers**](docs/StakingApi.md#get_providers) | **GET** /staking/providers | List staking providers details
*StakingApi* | [**get_summary**](docs/StakingApi.md#get_summary) | **GET** /staking/positions/summary | Get staking summary details
*StakingApi* | [**get_summary_by_vault**](docs/StakingApi.md#get_summary_by_vault) | **GET** /staking/positions/summary/vaults | Get staking summary details by vault
*StakingApi* | [**merge_stake_accounts**](docs/StakingApi.md#merge_stake_accounts) | **POST** /staking/chains/{chainDescriptor}/merge | Merge Solana on stake accounts
*StakingApi* | [**split**](docs/StakingApi.md#split) | **POST** /staking/chains/{chainDescriptor}/split | Execute a Split operation on SOL/SOL_TEST stake account
*StakingApi* | [**stake**](docs/StakingApi.md#stake) | **POST** /staking/chains/{chainDescriptor}/stake | Initiate Stake Operation
*StakingApi* | [**unstake**](docs/StakingApi.md#unstake) | **POST** /staking/chains/{chainDescriptor}/unstake | Execute an Unstake operation
*StakingApi* | [**withdraw**](docs/StakingApi.md#withdraw) | **POST** /staking/chains/{chainDescriptor}/withdraw | Execute a Withdraw operation
*TagsApi* | [**create_tag**](docs/TagsApi.md#create_tag) | **POST** /tags | Create a tag
*TagsApi* | [**delete_tag**](docs/TagsApi.md#delete_tag) | **DELETE** /tags/{tagId} | Delete a tag
*TagsApi* | [**get_tag**](docs/TagsApi.md#get_tag) | **GET** /tags/{tagId} | Get a tag
*TagsApi* | [**get_tags**](docs/TagsApi.md#get_tags) | **GET** /tags | Get list of tags
*TagsApi* | [**update_tag**](docs/TagsApi.md#update_tag) | **PATCH** /tags/{tagId} | Update a tag
*TokenizationApi* | [**burn_collection_token**](docs/TokenizationApi.md#burn_collection_token) | **POST** /tokenization/collections/{id}/tokens/burn | Burn tokens
*TokenizationApi* | [**create_new_collection**](docs/TokenizationApi.md#create_new_collection) | **POST** /tokenization/collections | Create a new collection
*TokenizationApi* | [**deactivate_and_unlink_adapters**](docs/TokenizationApi.md#deactivate_and_unlink_adapters) | **DELETE** /tokenization/multichain/bridge/layerzero | Remove LayerZero adapters
*TokenizationApi* | [**deploy_and_link_adapters**](docs/TokenizationApi.md#deploy_and_link_adapters) | **POST** /tokenization/multichain/bridge/layerzero | Deploy LayerZero adapters
*TokenizationApi* | [**fetch_collection_token_details**](docs/TokenizationApi.md#fetch_collection_token_details) | **GET** /tokenization/collections/{id}/tokens/{tokenId} | Get collection token details
*TokenizationApi* | [**get_collection_by_id**](docs/TokenizationApi.md#get_collection_by_id) | **GET** /tokenization/collections/{id} | Get a collection by id
*TokenizationApi* | [**get_deployable_address**](docs/TokenizationApi.md#get_deployable_address) | **POST** /tokenization/multichain/deterministic_address | Get deterministic address for contract deployment
*TokenizationApi* | [**get_layer_zero_dvn_config**](docs/TokenizationApi.md#get_layer_zero_dvn_config) | **GET** /tokenization/multichain/bridge/layerzero/config/{adapterTokenLinkId}/dvns | Get LayerZero DVN configuration
*TokenizationApi* | [**get_layer_zero_peers**](docs/TokenizationApi.md#get_layer_zero_peers) | **GET** /tokenization/multichain/bridge/layerzero/config/{adapterTokenLinkId}/peers | Get LayerZero peers
*TokenizationApi* | [**get_linked_collections**](docs/TokenizationApi.md#get_linked_collections) | **GET** /tokenization/collections | Get collections
*TokenizationApi* | [**get_linked_token**](docs/TokenizationApi.md#get_linked_token) | **GET** /tokenization/tokens/{id} | Return a linked token
*TokenizationApi* | [**get_linked_tokens**](docs/TokenizationApi.md#get_linked_tokens) | **GET** /tokenization/tokens | List all linked tokens
*TokenizationApi* | [**issue_new_token**](docs/TokenizationApi.md#issue_new_token) | **POST** /tokenization/tokens | Issue a new token
*TokenizationApi* | [**issue_token_multi_chain**](docs/TokenizationApi.md#issue_token_multi_chain) | **POST** /tokenization/multichain/tokens | Issue a token on one or more blockchains
*TokenizationApi* | [**link**](docs/TokenizationApi.md#link) | **POST** /tokenization/tokens/link | Link a contract
*TokenizationApi* | [**mint_collection_token**](docs/TokenizationApi.md#mint_collection_token) | **POST** /tokenization/collections/{id}/tokens/mint | Mint tokens
*TokenizationApi* | [**re_issue_token_multi_chain**](docs/TokenizationApi.md#re_issue_token_multi_chain) | **POST** /tokenization/multichain/reissue/token/{tokenLinkId} | Reissue a multichain token
*TokenizationApi* | [**remove_layer_zero_peers**](docs/TokenizationApi.md#remove_layer_zero_peers) | **DELETE** /tokenization/multichain/bridge/layerzero/config/peers | Remove LayerZero peers
*TokenizationApi* | [**set_layer_zero_dvn_config**](docs/TokenizationApi.md#set_layer_zero_dvn_config) | **POST** /tokenization/multichain/bridge/layerzero/config/dvns | Set LayerZero DVN configuration
*TokenizationApi* | [**set_layer_zero_peers**](docs/TokenizationApi.md#set_layer_zero_peers) | **POST** /tokenization/multichain/bridge/layerzero/config/peers | Set LayerZero peers
*TokenizationApi* | [**unlink**](docs/TokenizationApi.md#unlink) | **DELETE** /tokenization/tokens/{id} | Unlink a token
*TokenizationApi* | [**unlink_collection**](docs/TokenizationApi.md#unlink_collection) | **DELETE** /tokenization/collections/{id} | Delete a collection link
*TokenizationApi* | [**validate_layer_zero_channel_config**](docs/TokenizationApi.md#validate_layer_zero_channel_config) | **GET** /tokenization/multichain/bridge/layerzero/validate | Validate LayerZero channel configuration
*TradingBetaApi* | [**create_order**](docs/TradingBetaApi.md#create_order) | **POST** /trading/orders | Create an order
*TradingBetaApi* | [**create_quote**](docs/TradingBetaApi.md#create_quote) | **POST** /trading/quotes | Create a quote
*TradingBetaApi* | [**get_order**](docs/TradingBetaApi.md#get_order) | **GET** /trading/orders/{orderId} | Get order details
*TradingBetaApi* | [**get_orders**](docs/TradingBetaApi.md#get_orders) | **GET** /trading/orders | Get orders
*TradingBetaApi* | [**get_trading_providers**](docs/TradingBetaApi.md#get_trading_providers) | **GET** /trading/providers | Get providers
*TransactionsApi* | [**cancel_transaction**](docs/TransactionsApi.md#cancel_transaction) | **POST** /transactions/{txId}/cancel | Cancel a transaction
*TransactionsApi* | [**create_transaction**](docs/TransactionsApi.md#create_transaction) | **POST** /transactions | Create a new transaction
*TransactionsApi* | [**drop_transaction**](docs/TransactionsApi.md#drop_transaction) | **POST** /transactions/{txId}/drop | Drop ETH transaction by ID
*TransactionsApi* | [**estimate_network_fee**](docs/TransactionsApi.md#estimate_network_fee) | **GET** /estimate_network_fee | Estimate the required fee for an asset
*TransactionsApi* | [**estimate_transaction_fee**](docs/TransactionsApi.md#estimate_transaction_fee) | **POST** /transactions/estimate_fee | Estimate transaction fee
*TransactionsApi* | [**freeze_transaction**](docs/TransactionsApi.md#freeze_transaction) | **POST** /transactions/{txId}/freeze | Freeze a transaction
*TransactionsApi* | [**get_transaction**](docs/TransactionsApi.md#get_transaction) | **GET** /transactions/{txId} | Find a specific transaction by Fireblocks transaction ID
*TransactionsApi* | [**get_transaction_by_external_id**](docs/TransactionsApi.md#get_transaction_by_external_id) | **GET** /transactions/external_tx_id/{externalTxId} | Find a specific transaction by external transaction ID
*TransactionsApi* | [**get_transactions**](docs/TransactionsApi.md#get_transactions) | **GET** /transactions | List transaction history
*TransactionsApi* | [**rescan_transactions_beta**](docs/TransactionsApi.md#rescan_transactions_beta) | **POST** /transactions/rescan | rescan array of transactions
*TransactionsApi* | [**set_confirmation_threshold_by_transaction_hash**](docs/TransactionsApi.md#set_confirmation_threshold_by_transaction_hash) | **POST** /txHash/{txHash}/set_confirmation_threshold | Set confirmation threshold by transaction hash
*TransactionsApi* | [**set_transaction_confirmation_threshold**](docs/TransactionsApi.md#set_transaction_confirmation_threshold) | **POST** /transactions/{txId}/set_confirmation_threshold | Set confirmation threshold by transaction ID
*TransactionsApi* | [**unfreeze_transaction**](docs/TransactionsApi.md#unfreeze_transaction) | **POST** /transactions/{txId}/unfreeze | Unfreeze a transaction
*TransactionsApi* | [**validate_address**](docs/TransactionsApi.md#validate_address) | **GET** /transactions/validate_address/{assetId}/{address} | Validate destination address
*TravelRuleApi* | [**get_vasp_for_vault**](docs/TravelRuleApi.md#get_vasp_for_vault) | **GET** /screening/travel_rule/vault/{vaultAccountId}/vasp | Get assigned VASP to vault
*TravelRuleApi* | [**get_vaspby_did**](docs/TravelRuleApi.md#get_vaspby_did) | **GET** /screening/travel_rule/vasp/{did} | Get VASP details
*TravelRuleApi* | [**get_vasps**](docs/TravelRuleApi.md#get_vasps) | **GET** /screening/travel_rule/vasp | Get All VASPs
*TravelRuleApi* | [**set_vasp_for_vault**](docs/TravelRuleApi.md#set_vasp_for_vault) | **POST** /screening/travel_rule/vault/{vaultAccountId}/vasp | Assign VASP to vault
*TravelRuleApi* | [**update_vasp**](docs/TravelRuleApi.md#update_vasp) | **PUT** /screening/travel_rule/vasp/update | Add jsonDidKey to VASP details
*TravelRuleApi* | [**validate_full_travel_rule_transaction**](docs/TravelRuleApi.md#validate_full_travel_rule_transaction) | **POST** /screening/travel_rule/transaction/validate/full | Validate Full Travel Rule Transaction
*UserGroupsBetaApi* | [**create_user_group**](docs/UserGroupsBetaApi.md#create_user_group) | **POST** /management/user_groups | Create user group
*UserGroupsBetaApi* | [**delete_user_group**](docs/UserGroupsBetaApi.md#delete_user_group) | **DELETE** /management/user_groups/{groupId} | Delete user group
*UserGroupsBetaApi* | [**get_user_group**](docs/UserGroupsBetaApi.md#get_user_group) | **GET** /management/user_groups/{groupId} | Get user group
*UserGroupsBetaApi* | [**get_user_groups**](docs/UserGroupsBetaApi.md#get_user_groups) | **GET** /management/user_groups | List user groups
*UserGroupsBetaApi* | [**update_user_group**](docs/UserGroupsBetaApi.md#update_user_group) | **PUT** /management/user_groups/{groupId} | Update user group
*UsersApi* | [**get_users**](docs/UsersApi.md#get_users) | **GET** /users | List users
*VaultsApi* | [**activate_asset_for_vault_account**](docs/VaultsApi.md#activate_asset_for_vault_account) | **POST** /vault/accounts/{vaultAccountId}/{assetId}/activate | Activate a wallet in a vault account
*VaultsApi* | [**attach_tags_to_vault_accounts**](docs/VaultsApi.md#attach_tags_to_vault_accounts) | **POST** /vault/accounts/attached_tags/attach | Attach tags to a vault accounts
*VaultsApi* | [**create_legacy_address**](docs/VaultsApi.md#create_legacy_address) | **POST** /vault/accounts/{vaultAccountId}/{assetId}/addresses/{addressId}/create_legacy | Convert a segwit address to legacy format
*VaultsApi* | [**create_multiple_accounts**](docs/VaultsApi.md#create_multiple_accounts) | **POST** /vault/accounts/bulk | Bulk creation of new vault accounts
*VaultsApi* | [**create_multiple_deposit_addresses**](docs/VaultsApi.md#create_multiple_deposit_addresses) | **POST** /vault/accounts/addresses/bulk | Bulk creation of new deposit addresses
*VaultsApi* | [**create_vault_account**](docs/VaultsApi.md#create_vault_account) | **POST** /vault/accounts | Create a new vault account
*VaultsApi* | [**create_vault_account_asset**](docs/VaultsApi.md#create_vault_account_asset) | **POST** /vault/accounts/{vaultAccountId}/{assetId} | Create a new wallet
*VaultsApi* | [**create_vault_account_asset_address**](docs/VaultsApi.md#create_vault_account_asset_address) | **POST** /vault/accounts/{vaultAccountId}/{assetId}/addresses | Create new asset deposit address
*VaultsApi* | [**detach_tags_from_vault_accounts**](docs/VaultsApi.md#detach_tags_from_vault_accounts) | **POST** /vault/accounts/attached_tags/detach | Detach tags from a vault accounts
*VaultsApi* | [**get_asset_wallets**](docs/VaultsApi.md#get_asset_wallets) | **GET** /vault/asset_wallets | List asset wallets (Paginated)
*VaultsApi* | [**get_create_multiple_deposit_addresses_job_status**](docs/VaultsApi.md#get_create_multiple_deposit_addresses_job_status) | **GET** /vault/accounts/addresses/bulk/{jobId} | Get job status of bulk creation of new deposit addresses
*VaultsApi* | [**get_create_multiple_vault_accounts_job_status**](docs/VaultsApi.md#get_create_multiple_vault_accounts_job_status) | **GET** /vault/accounts/bulk/{jobId} | Get job status of bulk creation of new vault accounts
*VaultsApi* | [**get_max_spendable_amount**](docs/VaultsApi.md#get_max_spendable_amount) | **GET** /vault/accounts/{vaultAccountId}/{assetId}/max_spendable_amount | Get the maximum spendable amount in a single transaction.
*VaultsApi* | [**get_paged_vault_accounts**](docs/VaultsApi.md#get_paged_vault_accounts) | **GET** /vault/accounts_paged | List vault accounts (Paginated)
*VaultsApi* | [**get_public_key_info**](docs/VaultsApi.md#get_public_key_info) | **GET** /vault/public_key_info | Get the public key information
*VaultsApi* | [**get_public_key_info_for_address**](docs/VaultsApi.md#get_public_key_info_for_address) | **GET** /vault/accounts/{vaultAccountId}/{assetId}/{change}/{addressIndex}/public_key_info | Get the public key for a vault account
*VaultsApi* | [**get_unspent_inputs**](docs/VaultsApi.md#get_unspent_inputs) | **GET** /vault/accounts/{vaultAccountId}/{assetId}/unspent_inputs | Get UTXO unspent inputs information
*VaultsApi* | [**get_vault_account**](docs/VaultsApi.md#get_vault_account) | **GET** /vault/accounts/{vaultAccountId} | Find a vault account by ID
*VaultsApi* | [**get_vault_account_asset**](docs/VaultsApi.md#get_vault_account_asset) | **GET** /vault/accounts/{vaultAccountId}/{assetId} | Get the asset balance for a vault account
*VaultsApi* | [**get_vault_account_asset_addresses_paginated**](docs/VaultsApi.md#get_vault_account_asset_addresses_paginated) | **GET** /vault/accounts/{vaultAccountId}/{assetId}/addresses_paginated | List addresses (Paginated)
*VaultsApi* | [**get_vault_assets**](docs/VaultsApi.md#get_vault_assets) | **GET** /vault/assets | Get asset balance for chosen assets
*VaultsApi* | [**get_vault_balance_by_asset**](docs/VaultsApi.md#get_vault_balance_by_asset) | **GET** /vault/assets/{assetId} | Get vault balance by asset
*VaultsApi* | [**hide_vault_account**](docs/VaultsApi.md#hide_vault_account) | **POST** /vault/accounts/{vaultAccountId}/hide | Hide a vault account in the console
*VaultsApi* | [**set_customer_ref_id_for_address**](docs/VaultsApi.md#set_customer_ref_id_for_address) | **POST** /vault/accounts/{vaultAccountId}/{assetId}/addresses/{addressId}/set_customer_ref_id | Assign AML customer reference ID
*VaultsApi* | [**set_vault_account_auto_fuel**](docs/VaultsApi.md#set_vault_account_auto_fuel) | **POST** /vault/accounts/{vaultAccountId}/set_auto_fuel | Turn autofueling on or off
*VaultsApi* | [**set_vault_account_customer_ref_id**](docs/VaultsApi.md#set_vault_account_customer_ref_id) | **POST** /vault/accounts/{vaultAccountId}/set_customer_ref_id | Set an AML/KYT customer reference ID for a vault account
*VaultsApi* | [**unhide_vault_account**](docs/VaultsApi.md#unhide_vault_account) | **POST** /vault/accounts/{vaultAccountId}/unhide | Unhide a vault account in the console
*VaultsApi* | [**update_vault_account**](docs/VaultsApi.md#update_vault_account) | **PUT** /vault/accounts/{vaultAccountId} | Rename a vault account
*VaultsApi* | [**update_vault_account_asset_address**](docs/VaultsApi.md#update_vault_account_asset_address) | **PUT** /vault/accounts/{vaultAccountId}/{assetId}/addresses/{addressId} | Update address description
*VaultsApi* | [**update_vault_account_asset_balance**](docs/VaultsApi.md#update_vault_account_asset_balance) | **POST** /vault/accounts/{vaultAccountId}/{assetId}/balance | Refresh asset balance data
*Web3ConnectionsApi* | [**create**](docs/Web3ConnectionsApi.md#create) | **POST** /connections/wc | Create a new Web3 connection.
*Web3ConnectionsApi* | [**get**](docs/Web3ConnectionsApi.md#get) | **GET** /connections | List all open Web3 connections.
*Web3ConnectionsApi* | [**remove**](docs/Web3ConnectionsApi.md#remove) | **DELETE** /connections/wc/{id} | Remove an existing Web3 connection.
*Web3ConnectionsApi* | [**submit**](docs/Web3ConnectionsApi.md#submit) | **PUT** /connections/wc/{id} | Respond to a pending Web3 connection request.
*WebhooksApi* | [**resend_transaction_webhooks**](docs/WebhooksApi.md#resend_transaction_webhooks) | **POST** /webhooks/resend/{txId} | Resend failed webhooks for a transaction by ID
*WebhooksApi* | [**resend_webhooks**](docs/WebhooksApi.md#resend_webhooks) | **POST** /webhooks/resend | Resend failed webhooks
*WebhooksV2Api* | [**create_webhook**](docs/WebhooksV2Api.md#create_webhook) | **POST** /webhooks | Create new webhook
*WebhooksV2Api* | [**delete_webhook**](docs/WebhooksV2Api.md#delete_webhook) | **DELETE** /webhooks/{webhookId} | Delete webhook
*WebhooksV2Api* | [**get_notification**](docs/WebhooksV2Api.md#get_notification) | **GET** /webhooks/{webhookId}/notifications/{notificationId} | Get notification by id
*WebhooksV2Api* | [**get_notification_attempts**](docs/WebhooksV2Api.md#get_notification_attempts) | **GET** /webhooks/{webhookId}/notifications/{notificationId}/attempts | Get notification attempts
*WebhooksV2Api* | [**get_notifications**](docs/WebhooksV2Api.md#get_notifications) | **GET** /webhooks/{webhookId}/notifications | Get all notifications by webhook id
*WebhooksV2Api* | [**get_resend_job_status**](docs/WebhooksV2Api.md#get_resend_job_status) | **GET** /webhooks/{webhookId}/notifications/resend_failed/jobs/{jobId} | Get resend job status
*WebhooksV2Api* | [**get_webhook**](docs/WebhooksV2Api.md#get_webhook) | **GET** /webhooks/{webhookId} | Get webhook by id
*WebhooksV2Api* | [**get_webhooks**](docs/WebhooksV2Api.md#get_webhooks) | **GET** /webhooks | Get all webhooks
*WebhooksV2Api* | [**resend_failed_notifications**](docs/WebhooksV2Api.md#resend_failed_notifications) | **POST** /webhooks/{webhookId}/notifications/resend_failed | Resend failed notifications
*WebhooksV2Api* | [**resend_notification_by_id**](docs/WebhooksV2Api.md#resend_notification_by_id) | **POST** /webhooks/{webhookId}/notifications/{notificationId}/resend | Resend notification by id
*WebhooksV2Api* | [**resend_notifications_by_resource_id**](docs/WebhooksV2Api.md#resend_notifications_by_resource_id) | **POST** /webhooks/{webhookId}/notifications/resend_by_resource | Resend notifications by resource Id
*WebhooksV2Api* | [**update_webhook**](docs/WebhooksV2Api.md#update_webhook) | **PATCH** /webhooks/{webhookId} | Update webhook
*WorkspaceStatusBetaApi* | [**get_workspace_status**](docs/WorkspaceStatusBetaApi.md#get_workspace_status) | **GET** /management/workspace_status | Returns current workspace status
*WhitelistIpAddressesApi* | [**get_whitelist_ip_addresses**](docs/WhitelistIpAddressesApi.md#get_whitelist_ip_addresses) | **GET** /management/api_users/{userId}/whitelist_ip_addresses | Gets whitelisted ip addresses


## Documentation For Models

 - [APIUser](docs/APIUser.md)
 - [AbaPaymentInfo](docs/AbaPaymentInfo.md)
 - [AbiFunction](docs/AbiFunction.md)
 - [AccessType](docs/AccessType.md)
 - [Account](docs/Account.md)
 - [AccountAccess](docs/AccountAccess.md)
 - [AccountBase](docs/AccountBase.md)
 - [AccountBasedAccessProvider](docs/AccountBasedAccessProvider.md)
 - [AccountConfig](docs/AccountConfig.md)
 - [AccountHolderDetails](docs/AccountHolderDetails.md)
 - [AccountIdentifier](docs/AccountIdentifier.md)
 - [AccountProviderID](docs/AccountProviderID.md)
 - [AccountReference](docs/AccountReference.md)
 - [AccountType](docs/AccountType.md)
 - [AccountType2](docs/AccountType2.md)
 - [AchPaymentInfo](docs/AchPaymentInfo.md)
 - [AdapterProcessingResult](docs/AdapterProcessingResult.md)
 - [AddAbiRequestDto](docs/AddAbiRequestDto.md)
 - [AddAssetToExternalWalletRequest](docs/AddAssetToExternalWalletRequest.md)
 - [AddCollateralRequestBody](docs/AddCollateralRequestBody.md)
 - [AddContractAssetRequest](docs/AddContractAssetRequest.md)
 - [AddCosignerRequest](docs/AddCosignerRequest.md)
 - [AddCosignerResponse](docs/AddCosignerResponse.md)
 - [AddExchangeAccountRequest](docs/AddExchangeAccountRequest.md)
 - [AddExchangeAccountResponse](docs/AddExchangeAccountResponse.md)
 - [AdditionalInfo](docs/AdditionalInfo.md)
 - [AdditionalInfoRequest](docs/AdditionalInfoRequest.md)
 - [AdditionalInfoRequestAdditionalInfo](docs/AdditionalInfoRequestAdditionalInfo.md)
 - [AddressNotAvailableError](docs/AddressNotAvailableError.md)
 - [AmlRegistrationResult](docs/AmlRegistrationResult.md)
 - [AmlRegistrationResultFullPayload](docs/AmlRegistrationResultFullPayload.md)
 - [AmlScreeningResult](docs/AmlScreeningResult.md)
 - [AmlVerdictManualRequest](docs/AmlVerdictManualRequest.md)
 - [AmlVerdictManualResponse](docs/AmlVerdictManualResponse.md)
 - [AmountAndChainDescriptor](docs/AmountAndChainDescriptor.md)
 - [AmountInfo](docs/AmountInfo.md)
 - [AmountOverTimeConfig](docs/AmountOverTimeConfig.md)
 - [AmountOverTimeConfigRange](docs/AmountOverTimeConfigRange.md)
 - [AmountRange](docs/AmountRange.md)
 - [ApiKey](docs/ApiKey.md)
 - [ApiKeysPaginatedResponse](docs/ApiKeysPaginatedResponse.md)
 - [ApproversConfig](docs/ApproversConfig.md)
 - [ApproversConfigApprovalGroupsInner](docs/ApproversConfigApprovalGroupsInner.md)
 - [Asset](docs/Asset.md)
 - [AssetAlreadyExistHttpError](docs/AssetAlreadyExistHttpError.md)
 - [AssetAmount](docs/AssetAmount.md)
 - [AssetBadRequestErrorResponse](docs/AssetBadRequestErrorResponse.md)
 - [AssetClass](docs/AssetClass.md)
 - [AssetConfig](docs/AssetConfig.md)
 - [AssetConflictErrorResponse](docs/AssetConflictErrorResponse.md)
 - [AssetDetailsMetadata](docs/AssetDetailsMetadata.md)
 - [AssetDetailsOnchain](docs/AssetDetailsOnchain.md)
 - [AssetFeature](docs/AssetFeature.md)
 - [AssetForbiddenErrorResponse](docs/AssetForbiddenErrorResponse.md)
 - [AssetInternalServerErrorResponse](docs/AssetInternalServerErrorResponse.md)
 - [AssetMedia](docs/AssetMedia.md)
 - [AssetMediaAttributes](docs/AssetMediaAttributes.md)
 - [AssetMetadata](docs/AssetMetadata.md)
 - [AssetMetadataDto](docs/AssetMetadataDto.md)
 - [AssetMetadataRequest](docs/AssetMetadataRequest.md)
 - [AssetNotFoundErrorResponse](docs/AssetNotFoundErrorResponse.md)
 - [AssetNote](docs/AssetNote.md)
 - [AssetNoteRequest](docs/AssetNoteRequest.md)
 - [AssetOnchain](docs/AssetOnchain.md)
 - [AssetPriceForbiddenErrorResponse](docs/AssetPriceForbiddenErrorResponse.md)
 - [AssetPriceNotFoundErrorResponse](docs/AssetPriceNotFoundErrorResponse.md)
 - [AssetPriceResponse](docs/AssetPriceResponse.md)
 - [AssetResponse](docs/AssetResponse.md)
 - [AssetScope](docs/AssetScope.md)
 - [AssetTypeResponse](docs/AssetTypeResponse.md)
 - [AssetTypesConfigInner](docs/AssetTypesConfigInner.md)
 - [AssetWallet](docs/AssetWallet.md)
 - [AuditLogData](docs/AuditLogData.md)
 - [AuditorData](docs/AuditorData.md)
 - [AuthorizationGroups](docs/AuthorizationGroups.md)
 - [AuthorizationInfo](docs/AuthorizationInfo.md)
 - [BaseProvider](docs/BaseProvider.md)
 - [BasicAddressRequest](docs/BasicAddressRequest.md)
 - [BlockInfo](docs/BlockInfo.md)
 - [BlockchainExplorer](docs/BlockchainExplorer.md)
 - [BlockchainMedia](docs/BlockchainMedia.md)
 - [BlockchainMetadata](docs/BlockchainMetadata.md)
 - [BlockchainNotFoundErrorResponse](docs/BlockchainNotFoundErrorResponse.md)
 - [BlockchainOnchain](docs/BlockchainOnchain.md)
 - [BlockchainResponse](docs/BlockchainResponse.md)
 - [BlockchainTransfer](docs/BlockchainTransfer.md)
 - [BpsFee](docs/BpsFee.md)
 - [BusinessIdentification](docs/BusinessIdentification.md)
 - [CallbackHandler](docs/CallbackHandler.md)
 - [CallbackHandlerRequest](docs/CallbackHandlerRequest.md)
 - [CancelTransactionResponse](docs/CancelTransactionResponse.md)
 - [Capability](docs/Capability.md)
 - [ChainDescriptor](docs/ChainDescriptor.md)
 - [ChainInfoResponse](docs/ChainInfoResponse.md)
 - [ChannelDvnConfigWithConfirmations](docs/ChannelDvnConfigWithConfirmations.md)
 - [ChannelDvnConfigWithConfirmationsReceiveConfig](docs/ChannelDvnConfigWithConfirmationsReceiveConfig.md)
 - [ChannelDvnConfigWithConfirmationsSendConfig](docs/ChannelDvnConfigWithConfirmationsSendConfig.md)
 - [ClaimRewardsRequest](docs/ClaimRewardsRequest.md)
 - [CollectionBurnRequestDto](docs/CollectionBurnRequestDto.md)
 - [CollectionBurnResponseDto](docs/CollectionBurnResponseDto.md)
 - [CollectionDeployRequestDto](docs/CollectionDeployRequestDto.md)
 - [CollectionLinkDto](docs/CollectionLinkDto.md)
 - [CollectionMetadataDto](docs/CollectionMetadataDto.md)
 - [CollectionMintRequestDto](docs/CollectionMintRequestDto.md)
 - [CollectionMintResponseDto](docs/CollectionMintResponseDto.md)
 - [CollectionOwnershipResponse](docs/CollectionOwnershipResponse.md)
 - [CollectionTokenMetadataAttributeDto](docs/CollectionTokenMetadataAttributeDto.md)
 - [CollectionTokenMetadataDto](docs/CollectionTokenMetadataDto.md)
 - [CollectionType](docs/CollectionType.md)
 - [CommittedQuoteType](docs/CommittedQuoteType.md)
 - [ComplianceResultFullPayload](docs/ComplianceResultFullPayload.md)
 - [ComplianceResultStatusesEnum](docs/ComplianceResultStatusesEnum.md)
 - [ComplianceResults](docs/ComplianceResults.md)
 - [ComplianceScreeningResult](docs/ComplianceScreeningResult.md)
 - [ComplianceScreeningResultFullPayload](docs/ComplianceScreeningResultFullPayload.md)
 - [ConfigChangeRequestStatus](docs/ConfigChangeRequestStatus.md)
 - [ConfigConversionOperationSnapshot](docs/ConfigConversionOperationSnapshot.md)
 - [ConfigDisbursementOperationSnapshot](docs/ConfigDisbursementOperationSnapshot.md)
 - [ConfigOperation](docs/ConfigOperation.md)
 - [ConfigOperationSnapshot](docs/ConfigOperationSnapshot.md)
 - [ConfigOperationStatus](docs/ConfigOperationStatus.md)
 - [ConfigTransferOperationSnapshot](docs/ConfigTransferOperationSnapshot.md)
 - [ConnectedAccount](docs/ConnectedAccount.md)
 - [ConnectedAccountApprovalStatus](docs/ConnectedAccountApprovalStatus.md)
 - [ConnectedAccountAssetType](docs/ConnectedAccountAssetType.md)
 - [ConnectedAccountBalances](docs/ConnectedAccountBalances.md)
 - [ConnectedAccountBalancesResponse](docs/ConnectedAccountBalancesResponse.md)
 - [ConnectedAccountCapability](docs/ConnectedAccountCapability.md)
 - [ConnectedAccountManifest](docs/ConnectedAccountManifest.md)
 - [ConnectedAccountRateResponse](docs/ConnectedAccountRateResponse.md)
 - [ConnectedAccountTotalBalance](docs/ConnectedAccountTotalBalance.md)
 - [ConnectedAccountTradingPair](docs/ConnectedAccountTradingPair.md)
 - [ConnectedAccountTradingPairSupportedType](docs/ConnectedAccountTradingPairSupportedType.md)
 - [ConnectedAccountTradingPairsResponse](docs/ConnectedAccountTradingPairsResponse.md)
 - [ConnectedAccountsResponse](docs/ConnectedAccountsResponse.md)
 - [ConnectedSingleAccount](docs/ConnectedSingleAccount.md)
 - [ConnectedSingleAccountResponse](docs/ConnectedSingleAccountResponse.md)
 - [ConsoleUser](docs/ConsoleUser.md)
 - [ContractAbiResponseDto](docs/ContractAbiResponseDto.md)
 - [ContractAbiResponseDtoAbiInner](docs/ContractAbiResponseDtoAbiInner.md)
 - [ContractAttributes](docs/ContractAttributes.md)
 - [ContractDataDecodeDataType](docs/ContractDataDecodeDataType.md)
 - [ContractDataDecodeError](docs/ContractDataDecodeError.md)
 - [ContractDataDecodeRequest](docs/ContractDataDecodeRequest.md)
 - [ContractDataDecodeRequestData](docs/ContractDataDecodeRequestData.md)
 - [ContractDataDecodeResponseParams](docs/ContractDataDecodeResponseParams.md)
 - [ContractDataDecodedResponse](docs/ContractDataDecodedResponse.md)
 - [ContractDataLogDataParam](docs/ContractDataLogDataParam.md)
 - [ContractDeployRequest](docs/ContractDeployRequest.md)
 - [ContractDeployResponse](docs/ContractDeployResponse.md)
 - [ContractDoc](docs/ContractDoc.md)
 - [ContractMetadataDto](docs/ContractMetadataDto.md)
 - [ContractMethodConfig](docs/ContractMethodConfig.md)
 - [ContractMethodPattern](docs/ContractMethodPattern.md)
 - [ContractTemplateDto](docs/ContractTemplateDto.md)
 - [ContractUploadRequest](docs/ContractUploadRequest.md)
 - [ContractWithAbiDto](docs/ContractWithAbiDto.md)
 - [ConversionConfigOperation](docs/ConversionConfigOperation.md)
 - [ConversionOperationConfigParams](docs/ConversionOperationConfigParams.md)
 - [ConversionOperationExecution](docs/ConversionOperationExecution.md)
 - [ConversionOperationExecutionOutput](docs/ConversionOperationExecutionOutput.md)
 - [ConversionOperationExecutionParams](docs/ConversionOperationExecutionParams.md)
 - [ConversionOperationExecutionParamsExecutionParams](docs/ConversionOperationExecutionParamsExecutionParams.md)
 - [ConversionOperationFailure](docs/ConversionOperationFailure.md)
 - [ConversionOperationPreview](docs/ConversionOperationPreview.md)
 - [ConversionOperationPreviewOutput](docs/ConversionOperationPreviewOutput.md)
 - [ConversionOperationType](docs/ConversionOperationType.md)
 - [ConversionValidationFailure](docs/ConversionValidationFailure.md)
 - [ConvertAssetsRequest](docs/ConvertAssetsRequest.md)
 - [ConvertAssetsResponse](docs/ConvertAssetsResponse.md)
 - [Cosigner](docs/Cosigner.md)
 - [CosignersPaginatedResponse](docs/CosignersPaginatedResponse.md)
 - [CreateAPIUser](docs/CreateAPIUser.md)
 - [CreateAddressRequest](docs/CreateAddressRequest.md)
 - [CreateAddressResponse](docs/CreateAddressResponse.md)
 - [CreateAssetsBulkRequest](docs/CreateAssetsBulkRequest.md)
 - [CreateAssetsRequest](docs/CreateAssetsRequest.md)
 - [CreateConfigOperationRequest](docs/CreateConfigOperationRequest.md)
 - [CreateConnectionRequest](docs/CreateConnectionRequest.md)
 - [CreateConnectionResponse](docs/CreateConnectionResponse.md)
 - [CreateConsoleUser](docs/CreateConsoleUser.md)
 - [CreateContractRequest](docs/CreateContractRequest.md)
 - [CreateConversionConfigOperationRequest](docs/CreateConversionConfigOperationRequest.md)
 - [CreateDisbursementConfigOperationRequest](docs/CreateDisbursementConfigOperationRequest.md)
 - [CreateInternalTransferRequest](docs/CreateInternalTransferRequest.md)
 - [CreateInternalWalletAssetRequest](docs/CreateInternalWalletAssetRequest.md)
 - [CreateMultichainTokenRequest](docs/CreateMultichainTokenRequest.md)
 - [CreateMultichainTokenRequestCreateParams](docs/CreateMultichainTokenRequestCreateParams.md)
 - [CreateMultipleAccountsRequest](docs/CreateMultipleAccountsRequest.md)
 - [CreateMultipleDepositAddressesJobStatus](docs/CreateMultipleDepositAddressesJobStatus.md)
 - [CreateMultipleDepositAddressesRequest](docs/CreateMultipleDepositAddressesRequest.md)
 - [CreateMultipleVaultAccountsJobStatus](docs/CreateMultipleVaultAccountsJobStatus.md)
 - [CreateNcwConnectionRequest](docs/CreateNcwConnectionRequest.md)
 - [CreateNetworkIdRequest](docs/CreateNetworkIdRequest.md)
 - [CreateOrderRequest](docs/CreateOrderRequest.md)
 - [CreatePayoutRequest](docs/CreatePayoutRequest.md)
 - [CreateQuote](docs/CreateQuote.md)
 - [CreateQuoteScopeInner](docs/CreateQuoteScopeInner.md)
 - [CreateSigningKeyDto](docs/CreateSigningKeyDto.md)
 - [CreateSigningKeyDtoProofOfOwnership](docs/CreateSigningKeyDtoProofOfOwnership.md)
 - [CreateTagRequest](docs/CreateTagRequest.md)
 - [CreateTokenRequestDto](docs/CreateTokenRequestDto.md)
 - [CreateTokenRequestDtoCreateParams](docs/CreateTokenRequestDtoCreateParams.md)
 - [CreateTransactionResponse](docs/CreateTransactionResponse.md)
 - [CreateTransferConfigOperationRequest](docs/CreateTransferConfigOperationRequest.md)
 - [CreateUserGroupResponse](docs/CreateUserGroupResponse.md)
 - [CreateValidationKeyDto](docs/CreateValidationKeyDto.md)
 - [CreateValidationKeyResponseDto](docs/CreateValidationKeyResponseDto.md)
 - [CreateVaultAccountConnectionRequest](docs/CreateVaultAccountConnectionRequest.md)
 - [CreateVaultAccountRequest](docs/CreateVaultAccountRequest.md)
 - [CreateVaultAssetResponse](docs/CreateVaultAssetResponse.md)
 - [CreateWalletRequest](docs/CreateWalletRequest.md)
 - [CreateWebhookRequest](docs/CreateWebhookRequest.md)
 - [CreateWorkflowExecutionRequestParamsInner](docs/CreateWorkflowExecutionRequestParamsInner.md)
 - [CustomRoutingDest](docs/CustomRoutingDest.md)
 - [DVPSettlement](docs/DVPSettlement.md)
 - [DefaultNetworkRoutingDest](docs/DefaultNetworkRoutingDest.md)
 - [Delegation](docs/Delegation.md)
 - [DelegationSummary](docs/DelegationSummary.md)
 - [DeleteNetworkConnectionResponse](docs/DeleteNetworkConnectionResponse.md)
 - [DeleteNetworkIdResponse](docs/DeleteNetworkIdResponse.md)
 - [DeployLayerZeroAdaptersRequest](docs/DeployLayerZeroAdaptersRequest.md)
 - [DeployableAddressResponse](docs/DeployableAddressResponse.md)
 - [DeployedContractNotFoundError](docs/DeployedContractNotFoundError.md)
 - [DeployedContractResponseDto](docs/DeployedContractResponseDto.md)
 - [DeployedContractsPaginatedResponse](docs/DeployedContractsPaginatedResponse.md)
 - [DepositFundsFromLinkedDDAResponse](docs/DepositFundsFromLinkedDDAResponse.md)
 - [DerivationPathConfig](docs/DerivationPathConfig.md)
 - [DesignatedSignersConfig](docs/DesignatedSignersConfig.md)
 - [Destination](docs/Destination.md)
 - [DestinationConfig](docs/DestinationConfig.md)
 - [DestinationTransferPeerPath](docs/DestinationTransferPeerPath.md)
 - [DestinationTransferPeerPathResponse](docs/DestinationTransferPeerPathResponse.md)
 - [DirectAccess](docs/DirectAccess.md)
 - [DirectAccessProvider](docs/DirectAccessProvider.md)
 - [DisbursementAmountInstruction](docs/DisbursementAmountInstruction.md)
 - [DisbursementConfigOperation](docs/DisbursementConfigOperation.md)
 - [DisbursementInstruction](docs/DisbursementInstruction.md)
 - [DisbursementInstructionOutput](docs/DisbursementInstructionOutput.md)
 - [DisbursementOperationConfigParams](docs/DisbursementOperationConfigParams.md)
 - [DisbursementOperationExecution](docs/DisbursementOperationExecution.md)
 - [DisbursementOperationExecutionOutput](docs/DisbursementOperationExecutionOutput.md)
 - [DisbursementOperationExecutionParams](docs/DisbursementOperationExecutionParams.md)
 - [DisbursementOperationExecutionParamsExecutionParams](docs/DisbursementOperationExecutionParamsExecutionParams.md)
 - [DisbursementOperationInput](docs/DisbursementOperationInput.md)
 - [DisbursementOperationPreview](docs/DisbursementOperationPreview.md)
 - [DisbursementOperationPreviewOutput](docs/DisbursementOperationPreviewOutput.md)
 - [DisbursementOperationPreviewOutputInstructionSetInner](docs/DisbursementOperationPreviewOutputInstructionSetInner.md)
 - [DisbursementOperationType](docs/DisbursementOperationType.md)
 - [DisbursementPercentageInstruction](docs/DisbursementPercentageInstruction.md)
 - [DisbursementValidationFailure](docs/DisbursementValidationFailure.md)
 - [DispatchPayoutResponse](docs/DispatchPayoutResponse.md)
 - [DraftResponse](docs/DraftResponse.md)
 - [DraftReviewAndValidationResponse](docs/DraftReviewAndValidationResponse.md)
 - [DropTransactionRequest](docs/DropTransactionRequest.md)
 - [DropTransactionResponse](docs/DropTransactionResponse.md)
 - [DvnConfig](docs/DvnConfig.md)
 - [DvnConfigWithConfirmations](docs/DvnConfigWithConfirmations.md)
 - [EVMTokenCreateParamsDto](docs/EVMTokenCreateParamsDto.md)
 - [EditGasStationConfigurationResponse](docs/EditGasStationConfigurationResponse.md)
 - [EmbeddedWallet](docs/EmbeddedWallet.md)
 - [EmbeddedWalletAccount](docs/EmbeddedWalletAccount.md)
 - [EmbeddedWalletAddressDetails](docs/EmbeddedWalletAddressDetails.md)
 - [EmbeddedWalletAlgoritm](docs/EmbeddedWalletAlgoritm.md)
 - [EmbeddedWalletAssetBalance](docs/EmbeddedWalletAssetBalance.md)
 - [EmbeddedWalletAssetResponse](docs/EmbeddedWalletAssetResponse.md)
 - [EmbeddedWalletAssetRewardInfo](docs/EmbeddedWalletAssetRewardInfo.md)
 - [EmbeddedWalletDevice](docs/EmbeddedWalletDevice.md)
 - [EmbeddedWalletDeviceKeySetupResponse](docs/EmbeddedWalletDeviceKeySetupResponse.md)
 - [EmbeddedWalletDeviceKeySetupResponseSetupStatusInner](docs/EmbeddedWalletDeviceKeySetupResponseSetupStatusInner.md)
 - [EmbeddedWalletLatestBackupKey](docs/EmbeddedWalletLatestBackupKey.md)
 - [EmbeddedWalletLatestBackupResponse](docs/EmbeddedWalletLatestBackupResponse.md)
 - [EmbeddedWalletPaginatedAddressesResponse](docs/EmbeddedWalletPaginatedAddressesResponse.md)
 - [EmbeddedWalletPaginatedAssetsResponse](docs/EmbeddedWalletPaginatedAssetsResponse.md)
 - [EmbeddedWalletPaginatedWalletsResponse](docs/EmbeddedWalletPaginatedWalletsResponse.md)
 - [EmbeddedWalletSetUpStatus](docs/EmbeddedWalletSetUpStatus.md)
 - [ErrorCodes](docs/ErrorCodes.md)
 - [ErrorResponse](docs/ErrorResponse.md)
 - [ErrorResponseError](docs/ErrorResponseError.md)
 - [ErrorSchema](docs/ErrorSchema.md)
 - [EstimatedFeeDetails](docs/EstimatedFeeDetails.md)
 - [EstimatedNetworkFeeResponse](docs/EstimatedNetworkFeeResponse.md)
 - [EstimatedTransactionFeeResponse](docs/EstimatedTransactionFeeResponse.md)
 - [ExchangeAccount](docs/ExchangeAccount.md)
 - [ExchangeAsset](docs/ExchangeAsset.md)
 - [ExchangeSettlementTransactionsResponse](docs/ExchangeSettlementTransactionsResponse.md)
 - [ExchangeTradingAccount](docs/ExchangeTradingAccount.md)
 - [ExchangeType](docs/ExchangeType.md)
 - [ExecutionConversionOperation](docs/ExecutionConversionOperation.md)
 - [ExecutionDisbursementOperation](docs/ExecutionDisbursementOperation.md)
 - [ExecutionOperationStatus](docs/ExecutionOperationStatus.md)
 - [ExecutionRequestBaseDetails](docs/ExecutionRequestBaseDetails.md)
 - [ExecutionRequestDetails](docs/ExecutionRequestDetails.md)
 - [ExecutionResponseBaseDetails](docs/ExecutionResponseBaseDetails.md)
 - [ExecutionResponseDetails](docs/ExecutionResponseDetails.md)
 - [ExecutionScreeningOperation](docs/ExecutionScreeningOperation.md)
 - [ExecutionStep](docs/ExecutionStep.md)
 - [ExecutionStepDetails](docs/ExecutionStepDetails.md)
 - [ExecutionStepError](docs/ExecutionStepError.md)
 - [ExecutionStepStatusEnum](docs/ExecutionStepStatusEnum.md)
 - [ExecutionStepType](docs/ExecutionStepType.md)
 - [ExecutionTransferOperation](docs/ExecutionTransferOperation.md)
 - [ExternalAccount](docs/ExternalAccount.md)
 - [ExternalWalletAsset](docs/ExternalWalletAsset.md)
 - [Fee](docs/Fee.md)
 - [FeeBreakdown](docs/FeeBreakdown.md)
 - [FeeBreakdownOneOf](docs/FeeBreakdownOneOf.md)
 - [FeeBreakdownOneOf1](docs/FeeBreakdownOneOf1.md)
 - [FeeInfo](docs/FeeInfo.md)
 - [FeeLevel](docs/FeeLevel.md)
 - [FeePayerInfo](docs/FeePayerInfo.md)
 - [FetchAbiRequestDto](docs/FetchAbiRequestDto.md)
 - [FiatAccount](docs/FiatAccount.md)
 - [FiatAccountType](docs/FiatAccountType.md)
 - [FiatAsset](docs/FiatAsset.md)
 - [FiatTransfer](docs/FiatTransfer.md)
 - [FixedFee](docs/FixedFee.md)
 - [FreezeTransactionResponse](docs/FreezeTransactionResponse.md)
 - [FunctionDoc](docs/FunctionDoc.md)
 - [Funds](docs/Funds.md)
 - [GasStationConfiguration](docs/GasStationConfiguration.md)
 - [GasStationConfigurationResponse](docs/GasStationConfigurationResponse.md)
 - [GasStationPropertiesResponse](docs/GasStationPropertiesResponse.md)
 - [GasslessStandardConfigurations](docs/GasslessStandardConfigurations.md)
 - [GasslessStandardConfigurationsGaslessStandardConfigurationsValue](docs/GasslessStandardConfigurationsGaslessStandardConfigurationsValue.md)
 - [GetAPIUsersResponse](docs/GetAPIUsersResponse.md)
 - [GetAuditLogsResponse](docs/GetAuditLogsResponse.md)
 - [GetConnectionsResponse](docs/GetConnectionsResponse.md)
 - [GetConsoleUsersResponse](docs/GetConsoleUsersResponse.md)
 - [GetDeployableAddressRequest](docs/GetDeployableAddressRequest.md)
 - [GetExchangeAccountsCredentialsPublicKeyResponse](docs/GetExchangeAccountsCredentialsPublicKeyResponse.md)
 - [GetFilterParameter](docs/GetFilterParameter.md)
 - [GetLayerZeroDvnConfigResponse](docs/GetLayerZeroDvnConfigResponse.md)
 - [GetLayerZeroPeersResponse](docs/GetLayerZeroPeersResponse.md)
 - [GetLinkedCollectionsPaginatedResponse](docs/GetLinkedCollectionsPaginatedResponse.md)
 - [GetMaxSpendableAmountResponse](docs/GetMaxSpendableAmountResponse.md)
 - [GetMpcKeysResponse](docs/GetMpcKeysResponse.md)
 - [GetNFTsResponse](docs/GetNFTsResponse.md)
 - [GetOrdersResponse](docs/GetOrdersResponse.md)
 - [GetOtaStatusResponse](docs/GetOtaStatusResponse.md)
 - [GetOwnershipTokensResponse](docs/GetOwnershipTokensResponse.md)
 - [GetPagedExchangeAccountsResponse](docs/GetPagedExchangeAccountsResponse.md)
 - [GetPagedExchangeAccountsResponsePaging](docs/GetPagedExchangeAccountsResponsePaging.md)
 - [GetSigningKeyResponseDto](docs/GetSigningKeyResponseDto.md)
 - [GetTransactionOperation](docs/GetTransactionOperation.md)
 - [GetValidationKeyResponseDto](docs/GetValidationKeyResponseDto.md)
 - [GetWhitelistIpAddressesResponse](docs/GetWhitelistIpAddressesResponse.md)
 - [GetWorkspaceStatusResponse](docs/GetWorkspaceStatusResponse.md)
 - [HttpContractDoesNotExistError](docs/HttpContractDoesNotExistError.md)
 - [IbanPaymentInfo](docs/IbanPaymentInfo.md)
 - [Identification](docs/Identification.md)
 - [IdlType](docs/IdlType.md)
 - [IndicativeQuoteType](docs/IndicativeQuoteType.md)
 - [InitiatorConfig](docs/InitiatorConfig.md)
 - [InitiatorConfigPattern](docs/InitiatorConfigPattern.md)
 - [InstructionAmount](docs/InstructionAmount.md)
 - [InternalReference](docs/InternalReference.md)
 - [InternalTransferResponse](docs/InternalTransferResponse.md)
 - [InvalidParamaterValueError](docs/InvalidParamaterValueError.md)
 - [Job](docs/Job.md)
 - [JobCreated](docs/JobCreated.md)
 - [LayerZeroAdapterCreateParams](docs/LayerZeroAdapterCreateParams.md)
 - [LbtPaymentInfo](docs/LbtPaymentInfo.md)
 - [LeanAbiFunction](docs/LeanAbiFunction.md)
 - [LeanContractDto](docs/LeanContractDto.md)
 - [LeanDeployedContractResponseDto](docs/LeanDeployedContractResponseDto.md)
 - [LegacyAmountAggregationTimePeriodMethod](docs/LegacyAmountAggregationTimePeriodMethod.md)
 - [LegacyDraftResponse](docs/LegacyDraftResponse.md)
 - [LegacyDraftReviewAndValidationResponse](docs/LegacyDraftReviewAndValidationResponse.md)
 - [LegacyPolicyAndValidationResponse](docs/LegacyPolicyAndValidationResponse.md)
 - [LegacyPolicyCheckResult](docs/LegacyPolicyCheckResult.md)
 - [LegacyPolicyMetadata](docs/LegacyPolicyMetadata.md)
 - [LegacyPolicyResponse](docs/LegacyPolicyResponse.md)
 - [LegacyPolicyRule](docs/LegacyPolicyRule.md)
 - [LegacyPolicyRuleAmount](docs/LegacyPolicyRuleAmount.md)
 - [LegacyPolicyRuleAmountAggregation](docs/LegacyPolicyRuleAmountAggregation.md)
 - [LegacyPolicyRuleAuthorizationGroups](docs/LegacyPolicyRuleAuthorizationGroups.md)
 - [LegacyPolicyRuleAuthorizationGroupsGroupsInner](docs/LegacyPolicyRuleAuthorizationGroupsGroupsInner.md)
 - [LegacyPolicyRuleCheckResult](docs/LegacyPolicyRuleCheckResult.md)
 - [LegacyPolicyRuleDesignatedSigners](docs/LegacyPolicyRuleDesignatedSigners.md)
 - [LegacyPolicyRuleDst](docs/LegacyPolicyRuleDst.md)
 - [LegacyPolicyRuleError](docs/LegacyPolicyRuleError.md)
 - [LegacyPolicyRuleOperators](docs/LegacyPolicyRuleOperators.md)
 - [LegacyPolicyRuleRawMessageSigning](docs/LegacyPolicyRuleRawMessageSigning.md)
 - [LegacyPolicyRuleRawMessageSigningDerivationPath](docs/LegacyPolicyRuleRawMessageSigningDerivationPath.md)
 - [LegacyPolicyRuleSrc](docs/LegacyPolicyRuleSrc.md)
 - [LegacyPolicyRules](docs/LegacyPolicyRules.md)
 - [LegacyPolicySrcOrDestSubType](docs/LegacyPolicySrcOrDestSubType.md)
 - [LegacyPolicySrcOrDestType](docs/LegacyPolicySrcOrDestType.md)
 - [LegacyPolicyStatus](docs/LegacyPolicyStatus.md)
 - [LegacyPolicyValidation](docs/LegacyPolicyValidation.md)
 - [LegacyPublishDraftRequest](docs/LegacyPublishDraftRequest.md)
 - [LegacyPublishResult](docs/LegacyPublishResult.md)
 - [LegacySrcOrDestAttributesInner](docs/LegacySrcOrDestAttributesInner.md)
 - [LimitExecutionRequestDetails](docs/LimitExecutionRequestDetails.md)
 - [LimitExecutionResponseDetails](docs/LimitExecutionResponseDetails.md)
 - [ListAssetsResponse](docs/ListAssetsResponse.md)
 - [ListBlockchainsResponse](docs/ListBlockchainsResponse.md)
 - [ListOwnedCollectionsResponse](docs/ListOwnedCollectionsResponse.md)
 - [ListOwnedTokensResponse](docs/ListOwnedTokensResponse.md)
 - [Manifest](docs/Manifest.md)
 - [MarketExecutionRequestDetails](docs/MarketExecutionRequestDetails.md)
 - [MarketExecutionResponseDetails](docs/MarketExecutionResponseDetails.md)
 - [MarketRequoteRequestDetails](docs/MarketRequoteRequestDetails.md)
 - [MediaEntityResponse](docs/MediaEntityResponse.md)
 - [MergeStakeAccountsRequest](docs/MergeStakeAccountsRequest.md)
 - [MergeStakeAccountsResponse](docs/MergeStakeAccountsResponse.md)
 - [ModifySigningKeyAgentIdDto](docs/ModifySigningKeyAgentIdDto.md)
 - [ModifySigningKeyDto](docs/ModifySigningKeyDto.md)
 - [ModifyValidationKeyDto](docs/ModifyValidationKeyDto.md)
 - [MomoPaymentInfo](docs/MomoPaymentInfo.md)
 - [MpcKey](docs/MpcKey.md)
 - [MultichainDeploymentMetadata](docs/MultichainDeploymentMetadata.md)
 - [NetworkChannel](docs/NetworkChannel.md)
 - [NetworkConnection](docs/NetworkConnection.md)
 - [NetworkConnectionResponse](docs/NetworkConnectionResponse.md)
 - [NetworkConnectionRoutingPolicyValue](docs/NetworkConnectionRoutingPolicyValue.md)
 - [NetworkConnectionStatus](docs/NetworkConnectionStatus.md)
 - [NetworkFee](docs/NetworkFee.md)
 - [NetworkId](docs/NetworkId.md)
 - [NetworkIdResponse](docs/NetworkIdResponse.md)
 - [NetworkIdRoutingPolicyValue](docs/NetworkIdRoutingPolicyValue.md)
 - [NetworkRecord](docs/NetworkRecord.md)
 - [NewAddress](docs/NewAddress.md)
 - [NoneNetworkRoutingDest](docs/NoneNetworkRoutingDest.md)
 - [NotFoundException](docs/NotFoundException.md)
 - [Notification](docs/Notification.md)
 - [NotificationAttempt](docs/NotificationAttempt.md)
 - [NotificationAttemptsPaginatedResponse](docs/NotificationAttemptsPaginatedResponse.md)
 - [NotificationPaginatedResponse](docs/NotificationPaginatedResponse.md)
 - [NotificationStatus](docs/NotificationStatus.md)
 - [NotificationWithData](docs/NotificationWithData.md)
 - [OneTimeAddress](docs/OneTimeAddress.md)
 - [OneTimeAddressAccount](docs/OneTimeAddressAccount.md)
 - [OneTimeAddressReference](docs/OneTimeAddressReference.md)
 - [OperationExecutionFailure](docs/OperationExecutionFailure.md)
 - [OrderDetails](docs/OrderDetails.md)
 - [OrderStatus](docs/OrderStatus.md)
 - [OrderSummary](docs/OrderSummary.md)
 - [PaginatedAddressResponse](docs/PaginatedAddressResponse.md)
 - [PaginatedAddressResponsePaging](docs/PaginatedAddressResponsePaging.md)
 - [PaginatedAssetWalletResponse](docs/PaginatedAssetWalletResponse.md)
 - [PaginatedAssetWalletResponsePaging](docs/PaginatedAssetWalletResponsePaging.md)
 - [PaginatedAssetsResponse](docs/PaginatedAssetsResponse.md)
 - [Paging](docs/Paging.md)
 - [PairApiKeyRequest](docs/PairApiKeyRequest.md)
 - [PairApiKeyResponse](docs/PairApiKeyResponse.md)
 - [Parameter](docs/Parameter.md)
 - [ParameterWithValue](docs/ParameterWithValue.md)
 - [ParticipantRelationshipType](docs/ParticipantRelationshipType.md)
 - [ParticipantsIdentification](docs/ParticipantsIdentification.md)
 - [PayeeAccount](docs/PayeeAccount.md)
 - [PayeeAccountResponse](docs/PayeeAccountResponse.md)
 - [PayeeAccountType](docs/PayeeAccountType.md)
 - [PaymentAccount](docs/PaymentAccount.md)
 - [PaymentAccountResponse](docs/PaymentAccountResponse.md)
 - [PaymentAccountType](docs/PaymentAccountType.md)
 - [PaymentInstructions](docs/PaymentInstructions.md)
 - [PayoutInitMethod](docs/PayoutInitMethod.md)
 - [PayoutInstruction](docs/PayoutInstruction.md)
 - [PayoutInstructionResponse](docs/PayoutInstructionResponse.md)
 - [PayoutInstructionState](docs/PayoutInstructionState.md)
 - [PayoutResponse](docs/PayoutResponse.md)
 - [PayoutState](docs/PayoutState.md)
 - [PayoutStatus](docs/PayoutStatus.md)
 - [PeerAdapterInfo](docs/PeerAdapterInfo.md)
 - [PeerType](docs/PeerType.md)
 - [PersonalIdentification](docs/PersonalIdentification.md)
 - [PersonalIdentificationFullName](docs/PersonalIdentificationFullName.md)
 - [PixPaymentInfo](docs/PixPaymentInfo.md)
 - [PlatformAccount](docs/PlatformAccount.md)
 - [Players](docs/Players.md)
 - [PolicyAndValidationResponse](docs/PolicyAndValidationResponse.md)
 - [PolicyCheckResult](docs/PolicyCheckResult.md)
 - [PolicyMetadata](docs/PolicyMetadata.md)
 - [PolicyOperator](docs/PolicyOperator.md)
 - [PolicyResponse](docs/PolicyResponse.md)
 - [PolicyRule](docs/PolicyRule.md)
 - [PolicyRuleCheckResult](docs/PolicyRuleCheckResult.md)
 - [PolicyRuleError](docs/PolicyRuleError.md)
 - [PolicyStatus](docs/PolicyStatus.md)
 - [PolicyType](docs/PolicyType.md)
 - [PolicyValidation](docs/PolicyValidation.md)
 - [PostOrderSettlement](docs/PostOrderSettlement.md)
 - [PostalAddress](docs/PostalAddress.md)
 - [PreScreening](docs/PreScreening.md)
 - [PrefundedSettlement](docs/PrefundedSettlement.md)
 - [ProgramCallConfig](docs/ProgramCallConfig.md)
 - [Provider](docs/Provider.md)
 - [ProviderID](docs/ProviderID.md)
 - [ProvidersListResponse](docs/ProvidersListResponse.md)
 - [PublicKeyInformation](docs/PublicKeyInformation.md)
 - [PublishDraftRequest](docs/PublishDraftRequest.md)
 - [PublishResult](docs/PublishResult.md)
 - [Quote](docs/Quote.md)
 - [QuoteExecutionRequestDetails](docs/QuoteExecutionRequestDetails.md)
 - [QuoteExecutionResponseDetails](docs/QuoteExecutionResponseDetails.md)
 - [QuoteExecutionWithRequoteRequestDetails](docs/QuoteExecutionWithRequoteRequestDetails.md)
 - [QuoteExecutionWithRequoteRequestDetailsAllOfReQuote](docs/QuoteExecutionWithRequoteRequestDetailsAllOfReQuote.md)
 - [QuoteExecutionWithRequoteResponseDetails](docs/QuoteExecutionWithRequoteResponseDetails.md)
 - [QuoteExecutionWithRequoteResponseDetailsAllOfReQuote](docs/QuoteExecutionWithRequoteResponseDetailsAllOfReQuote.md)
 - [QuotesResponse](docs/QuotesResponse.md)
 - [ReadAbiFunction](docs/ReadAbiFunction.md)
 - [ReadCallFunctionDto](docs/ReadCallFunctionDto.md)
 - [ReadCallFunctionDtoAbiFunction](docs/ReadCallFunctionDtoAbiFunction.md)
 - [RedeemFundsToLinkedDDAResponse](docs/RedeemFundsToLinkedDDAResponse.md)
 - [RegisterNewAssetRequest](docs/RegisterNewAssetRequest.md)
 - [ReissueMultichainTokenRequest](docs/ReissueMultichainTokenRequest.md)
 - [RelatedRequest](docs/RelatedRequest.md)
 - [RelatedTransaction](docs/RelatedTransaction.md)
 - [RemoveCollateralRequestBody](docs/RemoveCollateralRequestBody.md)
 - [RemoveLayerZeroAdapterFailedResult](docs/RemoveLayerZeroAdapterFailedResult.md)
 - [RemoveLayerZeroAdaptersRequest](docs/RemoveLayerZeroAdaptersRequest.md)
 - [RemoveLayerZeroAdaptersResponse](docs/RemoveLayerZeroAdaptersResponse.md)
 - [RemoveLayerZeroPeersRequest](docs/RemoveLayerZeroPeersRequest.md)
 - [RemoveLayerZeroPeersResponse](docs/RemoveLayerZeroPeersResponse.md)
 - [RenameCosigner](docs/RenameCosigner.md)
 - [RenameVaultAccountResponse](docs/RenameVaultAccountResponse.md)
 - [RescanTransaction](docs/RescanTransaction.md)
 - [ResendFailedNotificationsJobStatusResponse](docs/ResendFailedNotificationsJobStatusResponse.md)
 - [ResendFailedNotificationsRequest](docs/ResendFailedNotificationsRequest.md)
 - [ResendFailedNotificationsResponse](docs/ResendFailedNotificationsResponse.md)
 - [ResendNotificationsByResourceIdRequest](docs/ResendNotificationsByResourceIdRequest.md)
 - [ResendTransactionWebhooksRequest](docs/ResendTransactionWebhooksRequest.md)
 - [ResendWebhooksByTransactionIdResponse](docs/ResendWebhooksByTransactionIdResponse.md)
 - [ResendWebhooksResponse](docs/ResendWebhooksResponse.md)
 - [RespondToConnectionRequest](docs/RespondToConnectionRequest.md)
 - [RetryRequoteRequestDetails](docs/RetryRequoteRequestDetails.md)
 - [RewardInfo](docs/RewardInfo.md)
 - [RewardsInfo](docs/RewardsInfo.md)
 - [SOLAccount](docs/SOLAccount.md)
 - [SOLAccountWithValue](docs/SOLAccountWithValue.md)
 - [ScreeningConfigurationsRequest](docs/ScreeningConfigurationsRequest.md)
 - [ScreeningMetadataConfig](docs/ScreeningMetadataConfig.md)
 - [ScreeningOperationExecution](docs/ScreeningOperationExecution.md)
 - [ScreeningOperationExecutionOutput](docs/ScreeningOperationExecutionOutput.md)
 - [ScreeningOperationFailure](docs/ScreeningOperationFailure.md)
 - [ScreeningOperationType](docs/ScreeningOperationType.md)
 - [ScreeningPolicyResponse](docs/ScreeningPolicyResponse.md)
 - [ScreeningProviderRulesConfigurationResponse](docs/ScreeningProviderRulesConfigurationResponse.md)
 - [ScreeningUpdateConfigurations](docs/ScreeningUpdateConfigurations.md)
 - [ScreeningValidationFailure](docs/ScreeningValidationFailure.md)
 - [ScreeningVerdict](docs/ScreeningVerdict.md)
 - [ScreeningVerdictMatchedRule](docs/ScreeningVerdictMatchedRule.md)
 - [SearchNetworkIdsResponse](docs/SearchNetworkIdsResponse.md)
 - [SepaPaymentInfo](docs/SepaPaymentInfo.md)
 - [SessionDTO](docs/SessionDTO.md)
 - [SessionMetadata](docs/SessionMetadata.md)
 - [SetAdminQuorumThresholdRequest](docs/SetAdminQuorumThresholdRequest.md)
 - [SetAdminQuorumThresholdResponse](docs/SetAdminQuorumThresholdResponse.md)
 - [SetAssetPriceRequest](docs/SetAssetPriceRequest.md)
 - [SetAutoFuelRequest](docs/SetAutoFuelRequest.md)
 - [SetConfirmationsThresholdRequest](docs/SetConfirmationsThresholdRequest.md)
 - [SetConfirmationsThresholdResponse](docs/SetConfirmationsThresholdResponse.md)
 - [SetCustomerRefIdForAddressRequest](docs/SetCustomerRefIdForAddressRequest.md)
 - [SetCustomerRefIdRequest](docs/SetCustomerRefIdRequest.md)
 - [SetLayerZeroDvnConfigRequest](docs/SetLayerZeroDvnConfigRequest.md)
 - [SetLayerZeroDvnConfigResponse](docs/SetLayerZeroDvnConfigResponse.md)
 - [SetLayerZeroPeersRequest](docs/SetLayerZeroPeersRequest.md)
 - [SetLayerZeroPeersResponse](docs/SetLayerZeroPeersResponse.md)
 - [SetNetworkIdDiscoverabilityRequest](docs/SetNetworkIdDiscoverabilityRequest.md)
 - [SetNetworkIdNameRequest](docs/SetNetworkIdNameRequest.md)
 - [SetNetworkIdResponse](docs/SetNetworkIdResponse.md)
 - [SetNetworkIdRoutingPolicyRequest](docs/SetNetworkIdRoutingPolicyRequest.md)
 - [SetOtaStatusRequest](docs/SetOtaStatusRequest.md)
 - [SetOtaStatusResponse](docs/SetOtaStatusResponse.md)
 - [SetOtaStatusResponseOneOf](docs/SetOtaStatusResponseOneOf.md)
 - [SetRoutingPolicyRequest](docs/SetRoutingPolicyRequest.md)
 - [SetRoutingPolicyResponse](docs/SetRoutingPolicyResponse.md)
 - [Settlement](docs/Settlement.md)
 - [SettlementRequestBody](docs/SettlementRequestBody.md)
 - [SettlementResponse](docs/SettlementResponse.md)
 - [SettlementSourceAccount](docs/SettlementSourceAccount.md)
 - [SignedMessage](docs/SignedMessage.md)
 - [SignedMessageSignature](docs/SignedMessageSignature.md)
 - [SigningKeyDto](docs/SigningKeyDto.md)
 - [SmartTransferApproveTerm](docs/SmartTransferApproveTerm.md)
 - [SmartTransferBadRequestResponse](docs/SmartTransferBadRequestResponse.md)
 - [SmartTransferCoinStatistic](docs/SmartTransferCoinStatistic.md)
 - [SmartTransferCreateTicket](docs/SmartTransferCreateTicket.md)
 - [SmartTransferCreateTicketTerm](docs/SmartTransferCreateTicketTerm.md)
 - [SmartTransferForbiddenResponse](docs/SmartTransferForbiddenResponse.md)
 - [SmartTransferFundDvpTicket](docs/SmartTransferFundDvpTicket.md)
 - [SmartTransferFundTerm](docs/SmartTransferFundTerm.md)
 - [SmartTransferManuallyFundTerm](docs/SmartTransferManuallyFundTerm.md)
 - [SmartTransferNotFoundResponse](docs/SmartTransferNotFoundResponse.md)
 - [SmartTransferSetTicketExpiration](docs/SmartTransferSetTicketExpiration.md)
 - [SmartTransferSetTicketExternalId](docs/SmartTransferSetTicketExternalId.md)
 - [SmartTransferSetUserGroups](docs/SmartTransferSetUserGroups.md)
 - [SmartTransferStatistic](docs/SmartTransferStatistic.md)
 - [SmartTransferStatisticInflow](docs/SmartTransferStatisticInflow.md)
 - [SmartTransferStatisticOutflow](docs/SmartTransferStatisticOutflow.md)
 - [SmartTransferSubmitTicket](docs/SmartTransferSubmitTicket.md)
 - [SmartTransferTicket](docs/SmartTransferTicket.md)
 - [SmartTransferTicketFilteredResponse](docs/SmartTransferTicketFilteredResponse.md)
 - [SmartTransferTicketResponse](docs/SmartTransferTicketResponse.md)
 - [SmartTransferTicketTerm](docs/SmartTransferTicketTerm.md)
 - [SmartTransferTicketTermResponse](docs/SmartTransferTicketTermResponse.md)
 - [SmartTransferUpdateTicketTerm](docs/SmartTransferUpdateTicketTerm.md)
 - [SmartTransferUserGroups](docs/SmartTransferUserGroups.md)
 - [SmartTransferUserGroupsResponse](docs/SmartTransferUserGroupsResponse.md)
 - [SolParameter](docs/SolParameter.md)
 - [SolParameterWithValue](docs/SolParameterWithValue.md)
 - [SolanaBlockchainData](docs/SolanaBlockchainData.md)
 - [SolanaConfig](docs/SolanaConfig.md)
 - [SolanaInstruction](docs/SolanaInstruction.md)
 - [SolanaInstructionWithValue](docs/SolanaInstructionWithValue.md)
 - [SolanaSimpleCreateParams](docs/SolanaSimpleCreateParams.md)
 - [SourceTransferPeerPath](docs/SourceTransferPeerPath.md)
 - [SourceTransferPeerPathResponse](docs/SourceTransferPeerPathResponse.md)
 - [SpamOwnershipResponse](docs/SpamOwnershipResponse.md)
 - [SpamTokenResponse](docs/SpamTokenResponse.md)
 - [SpeiAdvancedPaymentInfo](docs/SpeiAdvancedPaymentInfo.md)
 - [SpeiBasicPaymentInfo](docs/SpeiBasicPaymentInfo.md)
 - [SplitRequest](docs/SplitRequest.md)
 - [SplitResponse](docs/SplitResponse.md)
 - [StakeRequest](docs/StakeRequest.md)
 - [StakeResponse](docs/StakeResponse.md)
 - [StakingProvider](docs/StakingProvider.md)
 - [Status](docs/Status.md)
 - [StellarRippleCreateParamsDto](docs/StellarRippleCreateParamsDto.md)
 - [SystemMessageInfo](docs/SystemMessageInfo.md)
 - [Tag](docs/Tag.md)
 - [TagsPagedResponse](docs/TagsPagedResponse.md)
 - [Task](docs/Task.md)
 - [TemplatesPaginatedResponse](docs/TemplatesPaginatedResponse.md)
 - [ThirdPartyRouting](docs/ThirdPartyRouting.md)
 - [TimeInForce](docs/TimeInForce.md)
 - [TimePeriodConfig](docs/TimePeriodConfig.md)
 - [TimePeriodMatchType](docs/TimePeriodMatchType.md)
 - [ToCollateralTransaction](docs/ToCollateralTransaction.md)
 - [ToExchangeTransaction](docs/ToExchangeTransaction.md)
 - [TokenCollectionResponse](docs/TokenCollectionResponse.md)
 - [TokenInfoNotFoundErrorResponse](docs/TokenInfoNotFoundErrorResponse.md)
 - [TokenLinkDto](docs/TokenLinkDto.md)
 - [TokenLinkDtoTokenMetadata](docs/TokenLinkDtoTokenMetadata.md)
 - [TokenLinkExistsHttpError](docs/TokenLinkExistsHttpError.md)
 - [TokenLinkNotMultichainCompatibleHttpError](docs/TokenLinkNotMultichainCompatibleHttpError.md)
 - [TokenLinkRequestDto](docs/TokenLinkRequestDto.md)
 - [TokenOwnershipResponse](docs/TokenOwnershipResponse.md)
 - [TokenOwnershipSpamUpdatePayload](docs/TokenOwnershipSpamUpdatePayload.md)
 - [TokenOwnershipStatusUpdatePayload](docs/TokenOwnershipStatusUpdatePayload.md)
 - [TokenResponse](docs/TokenResponse.md)
 - [TokensPaginatedResponse](docs/TokensPaginatedResponse.md)
 - [TradingAccountType](docs/TradingAccountType.md)
 - [TradingErrorResponse](docs/TradingErrorResponse.md)
 - [TradingErrorResponseError](docs/TradingErrorResponseError.md)
 - [TradingProvider](docs/TradingProvider.md)
 - [Transaction](docs/Transaction.md)
 - [TransactionFee](docs/TransactionFee.md)
 - [TransactionOperation](docs/TransactionOperation.md)
 - [TransactionReceiptResponse](docs/TransactionReceiptResponse.md)
 - [TransactionRequest](docs/TransactionRequest.md)
 - [TransactionRequestAmount](docs/TransactionRequestAmount.md)
 - [TransactionRequestDestination](docs/TransactionRequestDestination.md)
 - [TransactionRequestFee](docs/TransactionRequestFee.md)
 - [TransactionRequestGasLimit](docs/TransactionRequestGasLimit.md)
 - [TransactionRequestGasPrice](docs/TransactionRequestGasPrice.md)
 - [TransactionRequestNetworkFee](docs/TransactionRequestNetworkFee.md)
 - [TransactionRequestNetworkStaking](docs/TransactionRequestNetworkStaking.md)
 - [TransactionRequestPriorityFee](docs/TransactionRequestPriorityFee.md)
 - [TransactionResponse](docs/TransactionResponse.md)
 - [TransactionResponseContractCallDecodedData](docs/TransactionResponseContractCallDecodedData.md)
 - [TransactionResponseDestination](docs/TransactionResponseDestination.md)
 - [TransferConfigOperation](docs/TransferConfigOperation.md)
 - [TransferOperationConfigParams](docs/TransferOperationConfigParams.md)
 - [TransferOperationExecution](docs/TransferOperationExecution.md)
 - [TransferOperationExecutionOutput](docs/TransferOperationExecutionOutput.md)
 - [TransferOperationExecutionParams](docs/TransferOperationExecutionParams.md)
 - [TransferOperationExecutionParamsExecutionParams](docs/TransferOperationExecutionParamsExecutionParams.md)
 - [TransferOperationFailure](docs/TransferOperationFailure.md)
 - [TransferOperationFailureData](docs/TransferOperationFailureData.md)
 - [TransferOperationPreview](docs/TransferOperationPreview.md)
 - [TransferOperationPreviewOutput](docs/TransferOperationPreviewOutput.md)
 - [TransferOperationType](docs/TransferOperationType.md)
 - [TransferPeerPathSubType](docs/TransferPeerPathSubType.md)
 - [TransferPeerPathType](docs/TransferPeerPathType.md)
 - [TransferRail](docs/TransferRail.md)
 - [TransferReceipt](docs/TransferReceipt.md)
 - [TransferValidationFailure](docs/TransferValidationFailure.md)
 - [TravelRuleAddress](docs/TravelRuleAddress.md)
 - [TravelRuleCreateTransactionRequest](docs/TravelRuleCreateTransactionRequest.md)
 - [TravelRuleDateAndPlaceOfBirth](docs/TravelRuleDateAndPlaceOfBirth.md)
 - [TravelRuleGeographicAddress](docs/TravelRuleGeographicAddress.md)
 - [TravelRuleGetAllVASPsResponse](docs/TravelRuleGetAllVASPsResponse.md)
 - [TravelRuleIssuer](docs/TravelRuleIssuer.md)
 - [TravelRuleIssuers](docs/TravelRuleIssuers.md)
 - [TravelRuleLegalPerson](docs/TravelRuleLegalPerson.md)
 - [TravelRuleLegalPersonNameIdentifier](docs/TravelRuleLegalPersonNameIdentifier.md)
 - [TravelRuleNationalIdentification](docs/TravelRuleNationalIdentification.md)
 - [TravelRuleNaturalNameIdentifier](docs/TravelRuleNaturalNameIdentifier.md)
 - [TravelRuleNaturalPerson](docs/TravelRuleNaturalPerson.md)
 - [TravelRuleNaturalPersonNameIdentifier](docs/TravelRuleNaturalPersonNameIdentifier.md)
 - [TravelRuleOwnershipProof](docs/TravelRuleOwnershipProof.md)
 - [TravelRulePerson](docs/TravelRulePerson.md)
 - [TravelRulePiiIVMS](docs/TravelRulePiiIVMS.md)
 - [TravelRulePolicyRuleResponse](docs/TravelRulePolicyRuleResponse.md)
 - [TravelRuleTransactionBlockchainInfo](docs/TravelRuleTransactionBlockchainInfo.md)
 - [TravelRuleUpdateVASPDetails](docs/TravelRuleUpdateVASPDetails.md)
 - [TravelRuleVASP](docs/TravelRuleVASP.md)
 - [TravelRuleValidateDateAndPlaceOfBirth](docs/TravelRuleValidateDateAndPlaceOfBirth.md)
 - [TravelRuleValidateFullTransactionRequest](docs/TravelRuleValidateFullTransactionRequest.md)
 - [TravelRuleValidateGeographicAddress](docs/TravelRuleValidateGeographicAddress.md)
 - [TravelRuleValidateLegalPerson](docs/TravelRuleValidateLegalPerson.md)
 - [TravelRuleValidateLegalPersonNameIdentifier](docs/TravelRuleValidateLegalPersonNameIdentifier.md)
 - [TravelRuleValidateNationalIdentification](docs/TravelRuleValidateNationalIdentification.md)
 - [TravelRuleValidateNaturalNameIdentifier](docs/TravelRuleValidateNaturalNameIdentifier.md)
 - [TravelRuleValidateNaturalPerson](docs/TravelRuleValidateNaturalPerson.md)
 - [TravelRuleValidateNaturalPersonNameIdentifier](docs/TravelRuleValidateNaturalPersonNameIdentifier.md)
 - [TravelRuleValidatePerson](docs/TravelRuleValidatePerson.md)
 - [TravelRuleValidatePiiIVMS](docs/TravelRuleValidatePiiIVMS.md)
 - [TravelRuleValidateTransactionRequest](docs/TravelRuleValidateTransactionRequest.md)
 - [TravelRuleValidateTransactionResponse](docs/TravelRuleValidateTransactionResponse.md)
 - [TravelRuleVaspForVault](docs/TravelRuleVaspForVault.md)
 - [TxLog](docs/TxLog.md)
 - [UnfreezeTransactionResponse](docs/UnfreezeTransactionResponse.md)
 - [UnmanagedWallet](docs/UnmanagedWallet.md)
 - [UnspentInput](docs/UnspentInput.md)
 - [UnspentInputsResponse](docs/UnspentInputsResponse.md)
 - [UnstakeRequest](docs/UnstakeRequest.md)
 - [UpdateAssetUserMetadataRequest](docs/UpdateAssetUserMetadataRequest.md)
 - [UpdateCallbackHandlerRequest](docs/UpdateCallbackHandlerRequest.md)
 - [UpdateCallbackHandlerResponse](docs/UpdateCallbackHandlerResponse.md)
 - [UpdateDraftRequest](docs/UpdateDraftRequest.md)
 - [UpdateTagRequest](docs/UpdateTagRequest.md)
 - [UpdateTokenOwnershipStatusDto](docs/UpdateTokenOwnershipStatusDto.md)
 - [UpdateVaultAccountAssetAddressRequest](docs/UpdateVaultAccountAssetAddressRequest.md)
 - [UpdateVaultAccountRequest](docs/UpdateVaultAccountRequest.md)
 - [UpdateWebhookRequest](docs/UpdateWebhookRequest.md)
 - [UsWirePaymentInfo](docs/UsWirePaymentInfo.md)
 - [UserGroupCreateRequest](docs/UserGroupCreateRequest.md)
 - [UserGroupCreateResponse](docs/UserGroupCreateResponse.md)
 - [UserGroupResponse](docs/UserGroupResponse.md)
 - [UserGroupUpdateRequest](docs/UserGroupUpdateRequest.md)
 - [UserResponse](docs/UserResponse.md)
 - [UserRole](docs/UserRole.md)
 - [UserStatus](docs/UserStatus.md)
 - [UserType](docs/UserType.md)
 - [ValidateAddressResponse](docs/ValidateAddressResponse.md)
 - [ValidateLayerZeroChannelResponse](docs/ValidateLayerZeroChannelResponse.md)
 - [ValidatedTransactionsForRescan](docs/ValidatedTransactionsForRescan.md)
 - [ValidationKeyDto](docs/ValidationKeyDto.md)
 - [Validator](docs/Validator.md)
 - [VaultAccount](docs/VaultAccount.md)
 - [VaultAccountsPagedResponse](docs/VaultAccountsPagedResponse.md)
 - [VaultAccountsPagedResponsePaging](docs/VaultAccountsPagedResponsePaging.md)
 - [VaultAccountsTagAttachmentsRequest](docs/VaultAccountsTagAttachmentsRequest.md)
 - [VaultActionStatus](docs/VaultActionStatus.md)
 - [VaultAsset](docs/VaultAsset.md)
 - [VaultWalletAddress](docs/VaultWalletAddress.md)
 - [VendorDto](docs/VendorDto.md)
 - [VerdictConfig](docs/VerdictConfig.md)
 - [Version](docs/Version.md)
 - [WalletAsset](docs/WalletAsset.md)
 - [WalletAssetAdditionalInfo](docs/WalletAssetAdditionalInfo.md)
 - [Webhook](docs/Webhook.md)
 - [WebhookEvent](docs/WebhookEvent.md)
 - [WebhookPaginatedResponse](docs/WebhookPaginatedResponse.md)
 - [WithdrawRequest](docs/WithdrawRequest.md)
 - [WorkflowConfigStatus](docs/WorkflowConfigStatus.md)
 - [WorkflowConfigurationId](docs/WorkflowConfigurationId.md)
 - [WorkflowExecutionOperation](docs/WorkflowExecutionOperation.md)
 - [WriteAbiFunction](docs/WriteAbiFunction.md)
 - [WriteCallFunctionDto](docs/WriteCallFunctionDto.md)
 - [WriteCallFunctionDtoAbiFunction](docs/WriteCallFunctionDtoAbiFunction.md)
 - [WriteCallFunctionResponseDto](docs/WriteCallFunctionResponseDto.md)


<a id="documentation-for-authorization"></a>
## Documentation For Authorization


Authentication schemes defined for the API:
<a id="bearerTokenAuth"></a>
### bearerTokenAuth

- **Type**: Bearer authentication (JWT)

<a id="ApiKeyAuth"></a>
### ApiKeyAuth

- **Type**: API key
- **API key parameter name**: X-API-Key
- **Location**: HTTP header


## Author

support@fireblocks.com


