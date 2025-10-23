"""
hiero_sdk_python.tokens.token_dissociate_transaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the `TokenDissociateTransaction` class, which models
a Hedera network transaction to dissociate one or more tokens from an account.

Classes:
    TokenDissociateTransaction
        Builds, signs, and executes a token dissociate transaction. Inherits
        from the base `Transaction` class and encapsulates all necessary
        fields and methods to perform a token dissociation on Hedera.
"""
from typing import Optional, List

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_dissociate_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.tokens.token_id import TokenId

class TokenDissociateTransaction(Transaction):
    """
    Represents a token dissociate transaction on the Hedera network.

    This transaction dissociates the specified tokens with an account,
    meaning the account can no longer hold or transact with those tokens.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a token dissociate transaction.
    """

    def __init__(
        self,
        account_id: Optional[AccountId] = None,
        token_ids: Optional[List[TokenId]] = None
    ) -> None:
        """
        Initializes a new TokenDissociateTransaction instance with default values.
        Args:
            account_id (AccountId, optional): The ID of the account to dissociate tokens from
            token_ids (List[TokenId], optional): A list of token IDs to dissociate from the account
        """
        super().__init__()
        self.account_id: Optional[AccountId] = account_id
        self.token_ids: List[TokenId] = token_ids or []

        self._default_transaction_fee: int = 500_000_000

    def set_account_id(self, account_id: AccountId) -> "TokenDissociateTransaction":
        """ Sets the account ID for the token dissociation transaction. """
        self._require_not_frozen()
        self.account_id = account_id
        return self

    def add_token_id(self, token_id: TokenId) -> "TokenDissociateTransaction":
        """Adds a token ID to the list of tokens to dissociate from the account."""
        self._require_not_frozen()
        self.token_ids.append(token_id)
        return self

    def _build_proto_body(self) -> token_dissociate_pb2.TokenDissociateTransactionBody:
        """
        Returns the protobuf body for the token dissociate transaction.
        
        Returns:
            TokenDissociateTransactionBody: The protobuf body for this transaction.
            
        Raises:
            ValueError: If account ID or token IDs are not set.
        """
        if not self.account_id or not self.token_ids:
            raise ValueError("Account ID and token IDs must be set.")

        return token_dissociate_pb2.TokenDissociateTransactionBody(
            account=self.account_id._to_proto(),
            tokens=[token_id._to_proto() for token_id in self.token_ids]
        )
        
    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token dissociation.

        Returns:
            TransactionBody: The protobuf transaction body with token dissociate details.
        """
        token_dissociate_body = self._build_proto_body()
        transaction_body: transaction_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenDissociate.CopyFrom(token_dissociate_body)
        return transaction_body
        
    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this token dissociate transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        token_dissociate_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.tokenDissociate.CopyFrom(token_dissociate_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.dissociateTokens,
            query_func=None
        )
