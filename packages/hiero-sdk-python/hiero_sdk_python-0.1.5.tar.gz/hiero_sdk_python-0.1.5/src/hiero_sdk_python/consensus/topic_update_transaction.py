"""
This module provides the `TopicUpdateTransaction` class for updating consensus topics
on the Hedera network using the Hiero SDK.
"""
from typing import Union, Optional
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    consensus_update_topic_pb2,
    duration_pb2,
    timestamp_pb2,
    transaction_pb2
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.public_key import PublicKey

class TopicUpdateTransaction(Transaction):
    """Represents a transaction to update a consensus topic."""
    def __init__(
        self,
        topic_id: Optional[basic_types_pb2.TopicID] = None,
        memo: Optional[str] = None,
        admin_key: Optional[PublicKey] = None,
        submit_key: Optional[PublicKey] = None,
        auto_renew_period: Optional[Duration] = Duration(7890000),
        auto_renew_account: Optional[AccountId] = None,
        expiration_time: Optional[timestamp_pb2.Timestamp] = None,
    ) -> None:
        """
        Initializes a new instance of the TopicUpdateTransaction class.
        Args:
            topic_id (basic_types_pb2.TopicID): The ID of the topic to update.
            memo (str): The memo associated with the topic.
            admin_key (PublicKey): The admin key for the topic.
            submit_key (PublicKey): The submit key for the topic.
            auto_renew_period (Duration): The auto-renew period for the topic.
            auto_renew_account (AccountId): The account ID for auto-renewal.
            expiration_time (timestamp_pb2.Timestamp): The expiration time of the topic.
        """
        super().__init__()
        self.topic_id: Optional[basic_types_pb2.TopicID] = topic_id
        self.memo: str = memo or ""
        self.admin_key: Optional[PublicKey] = admin_key
        self.submit_key: Optional[PublicKey] = submit_key
        self.auto_renew_period: Optional[Duration] = auto_renew_period
        self.auto_renew_account: Optional[AccountId] = auto_renew_account
        self.expiration_time: Optional[timestamp_pb2.Timestamp] = expiration_time
        self.transaction_fee: int = 10_000_000

    def set_topic_id(self, topic_id: basic_types_pb2.TopicID) -> "TopicUpdateTransaction":
        """
        Sets the topic ID for the transaction.

        Args:
            topic_id: The topic ID to update.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.topic_id = topic_id
        return self

    def set_memo(self, memo: str) -> "TopicUpdateTransaction":
        """
        Sets the memo for the topic.

        Args:
            memo: The memo to set.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.memo = memo
        return self

    def set_admin_key(self, key: PublicKey) -> "TopicUpdateTransaction":
        """
        Sets the public admin key for the topic.

        Args:
            Publickey: The admin key to set.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.admin_key = key
        return self

    def set_submit_key(self, key: PublicKey) -> "TopicUpdateTransaction":
        """
        Sets the public submit key for the topic.

        Args:
            Publickey: The submit key to set.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.submit_key = key
        return self

    def set_auto_renew_period(self, seconds: Union[Duration, int]) -> "TopicUpdateTransaction":
        """
        Sets the auto-renew period for the topic.

        Args:
            seconds: The auto-renew period in seconds.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        if isinstance(seconds, int):
            self.auto_renew_period = Duration(seconds)
        elif isinstance(seconds, Duration):
            self.auto_renew_period = seconds
        else:
            raise TypeError("Duration of invalid type")
        return self

    def set_auto_renew_account(self, account_id: AccountId) -> "TopicUpdateTransaction":
        """
        Sets the auto-renew account for the topic.

        Args:
            account_id: The account ID to set as the auto-renew account.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.auto_renew_account = account_id
        return self

    def set_expiration_time(
            self,
            expiration_time: timestamp_pb2.Timestamp
    ) -> "TopicUpdateTransaction":
        """
        Sets the expiration time for the topic.

        Args:
            expiration_time: The expiration time to set.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.expiration_time = expiration_time
        return self

    def _build_proto_body(self) -> consensus_update_topic_pb2.ConsensusUpdateTopicTransactionBody:
        """
        Returns the protobuf body for the topic update transaction.
        
        Returns:
            ConsensusUpdateTopicTransactionBody: The protobuf body for this transaction.
            
        Raises:
            ValueError: If required fields are missing.
        """
        if self.topic_id is None:
            raise ValueError("Missing required fields: topic_id")

        return consensus_update_topic_pb2.ConsensusUpdateTopicTransactionBody(
            topicID=self.topic_id._to_proto(),
            adminKey=self.admin_key._to_proto() if self.admin_key else None,
            submitKey=self.submit_key._to_proto() if self.submit_key else None,
            autoRenewPeriod=(
                duration_pb2.Duration(seconds=self.auto_renew_period.seconds)
                if self.auto_renew_period else None
            ),
            autoRenewAccount=(
                self.auto_renew_account._to_proto()
                if self.auto_renew_account else None
            ),
            expirationTime=self.expiration_time._to_proto() if self.expiration_time else None,
            memo=_wrappers_pb2.StringValue(value=self.memo) if self.memo else None
        )

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for topic update.

        Returns:
            TransactionBody: The protobuf transaction body containing the topic update details.
        """
        consensus_update_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.consensusUpdateTopic.CopyFrom(consensus_update_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this topic update transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        consensus_update_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.consensusUpdateTopic.CopyFrom(consensus_update_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the method for executing the topic update transaction.
        Args:
            channel (_Channel): The channel to use for the transaction.
        Returns:
            _Method: The method to execute the transaction.
        """
        return _Method(
            transaction_func=channel.topic.updateTopic,
            query_func=None
        )
