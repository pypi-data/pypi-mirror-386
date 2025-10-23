"""
hiero_sdk_python.tokens.token_freeze_transaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenFreezeTransaction, a subclass of Transaction for freezing a specified token
for an account on the Hedera network using the Hedera Token Service (HTS) API.
"""
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_freeze_account_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TokenFreezeTransaction(Transaction):
    """
    Represents a token freeze transaction on the Hedera network.

    This transaction freezes a specified token for a given account.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a token freeze transaction.
    """

    def __init__(
            self,
            token_id: Optional[TokenId] = None,
            account_id: Optional[AccountId]=None
        ) -> None:
        """
        Initializes a new TokenFreezeTransaction instance with optional token_id and account_id.

        Args:
            token_id (TokenId, optional): The ID of the token to be frozen.
            account_id (AccountId, optional): The ID of the account to have their token frozen.
        """
        super().__init__()
        self.token_id: Optional[TokenId] = token_id
        self.account_id: Optional[AccountId] = account_id
        self._default_transaction_fee: int = 3_000_000_000

    def set_token_id(self, token_id: TokenId) -> "TokenFreezeTransaction":
        """
        Sets the ID of the token to be frozen.

        Args:
            token_id (TokenId): The ID of the token to be frozen.

        Returns:
            TokenFreezeTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self

    def set_account_id(self, account_id: AccountId) -> "TokenFreezeTransaction":
        """
        Sets the ID of the account to be frozen.

        Args:
            account_id (AccountId): The ID of the account to have their token frozen.

        Returns:
            TokenFreezeTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.account_id = account_id
        return self

    def _build_proto_body(self) -> token_freeze_account_pb2.TokenFreezeAccountTransactionBody:
        """
        Returns the protobuf body for the token freeze transaction.
        
        Returns:
            TokenFreezeAccountTransactionBody: The protobuf body for this transaction.
            
        Raises:
            ValueError: If the token ID or account ID is missing.
        """
        if not self.token_id:
            raise ValueError("Missing required TokenID.")

        if not self.account_id:
            raise ValueError("Missing required AccountID.")

        return token_freeze_account_pb2.TokenFreezeAccountTransactionBody(
            token=self.token_id._to_proto(),
            account=self.account_id._to_proto()
        )
        
    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token freeze.

        Returns:
            TransactionBody: The protobuf transaction body containing the token freeze details.
        """
        token_freeze_body = self._build_proto_body()
        transaction_body: transaction_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenFreeze.CopyFrom(token_freeze_body)
        return transaction_body
        
    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this token freeze transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        token_freeze_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.tokenFreeze.CopyFrom(token_freeze_body)
        return schedulable_body


    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.freezeTokenAccount,
            query_func=None
        )
