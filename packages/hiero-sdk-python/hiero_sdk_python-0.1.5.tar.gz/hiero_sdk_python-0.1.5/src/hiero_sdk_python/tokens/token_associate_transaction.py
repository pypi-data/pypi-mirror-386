"""
hiero_sdk_python.tokens.token_associate_transaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenAssociateTransaction, a subclass of Transaction for associating
tokens with accounts on the Hedera network using the Hedera Token Service (HTS) API.
"""
from typing import Optional, List

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import token_associate_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction import Transaction


class TokenAssociateTransaction(Transaction):
    """
    Represents a token associate transaction on the Hedera network.

    This transaction associates the specified tokens with an account,
    allowing the account to hold and transact with those tokens.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token association transaction.
    """

    def __init__(
            self,
            account_id: Optional[AccountId] = None,
            token_ids: Optional[List[TokenId]] = None
        ) -> None:
        """
        Initializes a new TokenAssociateTransaction instance with optional keyword arguments.

        Args:
            account_id (AccountId, optional): The account to associate tokens with.
            token_ids (list of TokenId, optional): The tokens to associate with the account.
        """
        super().__init__()
        self.account_id: Optional[AccountId] = account_id
        self.token_ids: List[TokenId] = list(token_ids) if token_ids is not None else []
        self._default_transaction_fee: int = 500_000_000

    def set_account_id(self, account_id: AccountId) -> "TokenAssociateTransaction":
        """        
        Sets the account ID for the token association transaction.
        Args:
            account_id (AccountId): The account ID to associate tokens with.
        Returns:
            TokenAssociateTransaction: The current instance for method chaining.
        """
        self._require_not_frozen()
        self.account_id = account_id
        return self

    def add_token_id(self, token_id: TokenId) -> "TokenAssociateTransaction":
        """Add a token ID to the association list."""
        self._require_not_frozen()
        self.token_ids.append(token_id)
        return self

    def _build_proto_body(self) -> token_associate_pb2.TokenAssociateTransactionBody:
        """
        Returns the protobuf body for the token associate transaction.
        
        Returns:
            TokenAssociateTransactionBody: The protobuf body for this transaction.
            
        Raises:
            ValueError: If account ID or token IDs are not set.
        """
        if not self.account_id or not self.token_ids:
            raise ValueError("Account ID and token IDs must be set.")

        return token_associate_pb2.TokenAssociateTransactionBody(
            account=self.account_id._to_proto(),
            tokens=[token_id._to_proto() for token_id in self.token_ids]
        )
        
    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token association.

        Returns:
            TransactionBody: The protobuf transaction body containing the token association details.
        """
        token_associate_body = self._build_proto_body()
        transaction_body: transaction_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenAssociate.CopyFrom(token_associate_body)

        return transaction_body
        
    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this token associate transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        token_associate_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.tokenAssociate.CopyFrom(token_associate_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.associateTokens,
            query_func=None
        )
