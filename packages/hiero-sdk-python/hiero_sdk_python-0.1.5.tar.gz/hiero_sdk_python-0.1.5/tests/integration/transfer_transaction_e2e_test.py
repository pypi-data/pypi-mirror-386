import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, create_nft_token

@pytest.mark.integration
def test_integration_transfer_transaction_can_transfer_hbar():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = Hbar(1)
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        assert account_id is not None
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_hbar_transfer(env.operator_id, -1)
        transfer_transaction.add_hbar_transfer(account_id, 1)
        
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Transfer failed with status: {ResponseCode(receipt.status).name}"
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)

        expected_balance_tinybars = Hbar(1).to_tinybars() + 1
        assert balance and balance.hbars.to_tinybars() == expected_balance_tinybars, f"Expected balance: {expected_balance_tinybars}, actual balance: {balance.hbars.to_tinybars()}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_transfer_transaction_can_transfer_token():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = Hbar(1)
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        assert account_id is not None
        
        token_id = create_fungible_token(env)
        assert token_id is not None
        
        associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[token_id]
        )
        
        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_token_transfer(token_id, env.operator_id, -1)
        transfer_transaction.add_token_transfer(token_id, account_id, 1)
        
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        assert balance is not None
    finally:
        env.close()
        
@pytest.mark.integration
def test_integration_token_transfer_transaction_can_transfer_nft():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = Hbar(1)
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        assert account_id is not None
        
        token_id = create_nft_token(env)
        assert token_id is not None
        
        mint_transaction = TokenMintTransaction(
            token_id=token_id,
            metadata=[b"test"]
        )
        
        receipt = mint_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT mint failed with status: {ResponseCode(receipt.status).name}"
        
        serial_number = receipt.serial_numbers[0]
        
        nft_id = NftId(token_id, serial_number)
        
        associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[token_id]
        )
        
        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT association failed with status: {ResponseCode(receipt.status).name}"
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_nft_transfer(nft_id, env.operator_id, account_id)
        
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT transfer failed with status: {ResponseCode(receipt.status).name}"
        
        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)
        
        # We check if the nft has transfered to the new account
        # For now, token_balances is a map so we check it this way
        assert balance and balance.token_balances == {token_id: serial_number}
    finally:
        env.close()

@pytest.mark.integration
def test_integration_transfer_transaction_transfer_hbar_nothing_set():
    env = IntegrationTestEnv()
    
    try:
        transfer_transaction = TransferTransaction()
        
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Transfer failed with status: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_transfer_transaction_transfer_wrong_hbar_amount():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = Hbar(1)
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        assert account_id is not None
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_hbar_transfer(env.operator_id, -1)
        transfer_transaction.add_hbar_transfer(account_id, 2)
        
        with pytest.raises(PrecheckError, match=f"Transaction failed precheck with status: INVALID_ACCOUNT_AMOUNTS"):
            transfer_transaction.execute(env.client)
    finally:
        env.close()

@pytest.mark.integration
def test_integration_transfer_transaction_transfer_hbar_fail_not_enough_balance():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = 1000
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Account 1"
        )
        
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_1_id = receipt.account_id
        assert account_1_id is not None

        transfer_transaction = TransferTransaction()
        transfer_transaction.add_hbar_transfer(account_1_id, -20000)
        transfer_transaction.add_hbar_transfer(env.operator_id, 20000)
        
        transfer_transaction.freeze_with(env.client)
        transfer_transaction.sign(new_account_private_key)
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.INSUFFICIENT_ACCOUNT_BALANCE, f"Transfer should have failed with INSUFFICIENT_ACCOUNT_BALANCE status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_transfer_transaction_fail_not_enough_balance():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = Hbar(1)
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        assert account_id is not None
        
        token_id = create_fungible_token(env)
        assert token_id is not None
        
        associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[token_id]
        )
        
        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_token_transfer(token_id, env.operator_id, -100000)
        transfer_transaction.add_token_transfer(token_id, account_id, 100000)
        
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.INSUFFICIENT_TOKEN_BALANCE, f"Token transfer should have failed with INSUFFICIENT_TOKEN_BALANCE status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_transfer_transaction_fail_not_your_nft():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = Hbar(1)
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        assert account_id is not None
        
        token_id = create_nft_token(env)
        assert token_id is not None
        
        mint_transaction = TokenMintTransaction(
            token_id=token_id,
            metadata=[b"test"]
        )
        
        receipt = mint_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT mint failed with status: {ResponseCode(receipt.status).name}"
        
        serial_number = receipt.serial_numbers[0]
        
        nft_id = NftId(token_id, serial_number)
        
        associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[token_id]
        )
        
        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT association failed with status: {ResponseCode(receipt.status).name}"
        
        transfer_transaction = TransferTransaction()
        transfer_transaction.add_nft_transfer(nft_id, account_id, env.operator_id)
        
        transfer_transaction.freeze_with(env.client)
        transfer_transaction.sign(new_account_private_key)
        receipt = transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SENDER_DOES_NOT_OWN_NFT_SERIAL_NO, f"NFT transfer should have failed with SENDER_DOES_NOT_OWN_NFT_SERIAL_NO status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()