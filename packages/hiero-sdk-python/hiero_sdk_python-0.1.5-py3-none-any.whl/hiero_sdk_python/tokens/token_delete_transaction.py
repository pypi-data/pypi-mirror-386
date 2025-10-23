"""
hiero_sdk_python.tokens.token_delete_transaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenDeleteTransaction, a subclass of Transaction for deleting tokens
on the Hedera network using the Hedera Token Service (HTS) API.
"""
from typing import Optional

from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_delete_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.tokens.token_id import TokenId

class TokenDeleteTransaction(Transaction):
    """
    Represents a token deletion transaction on the Hedera network.

    This transaction deletes a specified token, rendering it inactive.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a token deletion transaction.
    """

    def __init__(
            self,
            token_id: Optional[TokenId] = None
        ) -> None:
        """
        Initializes a new TokenDeleteTransaction instance with optional token_id.

        Args:
            token_id (TokenId, optional): The ID of the token to be deleted.
        """
        super().__init__()
        self.token_id: Optional[TokenId] = token_id
        self._default_transaction_fee: int = 3_000_000_000

    def set_token_id(self, token_id: TokenId) -> "TokenDeleteTransaction":
        """
        Sets the ID of the token to be deleted.

        Args:
            token_id (TokenId): The ID of the token to be deleted.

        Returns:
            TokenDeleteTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self

    def _build_proto_body(self) -> token_delete_pb2.TokenDeleteTransactionBody:
        """
        Returns the protobuf body for the token delete transaction.
        
        Returns:
            TokenDeleteTransactionBody: The protobuf body for this transaction.
            
        Raises:
            ValueError: If the token ID is missing.
        """
        if not self.token_id:
            raise ValueError("Missing required TokenID.")

        return token_delete_pb2.TokenDeleteTransactionBody(
            token=self.token_id._to_proto()
        )
        
    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token deletion.

        Returns:
            TransactionBody: The protobuf transaction body containing the token deletion details.
        """
        token_delete_body = self._build_proto_body()
        transaction_body: transaction_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.tokenDeletion.CopyFrom(token_delete_body)
        return transaction_body
        
    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this token delete transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        token_delete_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.tokenDeletion.CopyFrom(token_delete_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.deleteToken,
            query_func=None
        )
