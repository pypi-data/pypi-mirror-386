"""
transaction_response.py
~~~~~~~~~~~~~~~~~~~~~~~~

Represents the response from a transaction submitted to the Hedera network.
Provides methods to retrieve the receipt and access core transaction details.
"""
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.transaction.transaction_id import TransactionId
# pylint: disable=too-few-public-methods

class TransactionResponse:
    """
    Represents the response from a transaction submitted to the Hedera network.
    """

    def __init__(self) -> None:
        """
        Initialize a new TransactionResponse instance with default values.
        """
        self.transaction_id = TransactionId()
        self.node_id: AccountId = AccountId()
        self.hash: bytes = bytes()
        self.validate_status: bool = False
        self.transaction = None

    def get_receipt(self, client):
        """
        Retrieves the receipt for this transaction from the Hedera network.

        Args:
            client (Client): The client instance to use for receipt retrieval

        Returns:
            TransactionReceipt: The receipt from the network, containing the status
                               and any entities created by the transaction
        """
        # TODO: Decide how to avoid circular imports
        from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery
        # TODO: Implement set_node_account_ids() to get failure reason for preHandle failures
        receipt = (
            TransactionGetReceiptQuery()
            .set_transaction_id(self.transaction_id)
            .execute(client)
        )

        return receipt
