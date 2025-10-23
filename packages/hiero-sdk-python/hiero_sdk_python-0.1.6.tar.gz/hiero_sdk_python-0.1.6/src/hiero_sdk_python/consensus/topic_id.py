"""
This module defines the `TopicId` class, a utility for working with Hedera
Consensus Service (HCS) topic identifiers.

It provides methods for converting between protobuf `TopicID` objects and
string representations, making it easier to work with topics in different
formats within the Hiero SDK.
"""

from hiero_sdk_python.hapi.services import basic_types_pb2

class TopicId:

    """
    Represents the unique identifier of a topic in the Hedera Consensus Service (HCS).

    A `TopicId` consists of three components: shard, realm, and num.
    This class provides convenient methods for converting between Python objects,
    protobuf `TopicID` instances, and string formats.
    """
    def __init__(self, shard: int = 0, realm: int = 0, num: int = 0) -> None:
        """
        Initializes a new instance of the TopicId class.
        Args:
            shard (int): The shard number of the topic.
            realm (int): The realm number of the topic.
            num (int): The topic number.
        """
        self.shard: int = shard
        self.realm: int = realm
        self.num: int = num

    @classmethod
    def _from_proto(cls, topic_id_proto: basic_types_pb2.TopicID) -> "TopicId":
        """
        Creates a TopicId instance from a protobuf TopicID object.

        Args:
            topic_id_proto (basic_types_pb2.TopicID): The protobuf TopicID object.

        Returns:
            TopicId: A new TopicId instance.
        """
        return cls(
            shard=topic_id_proto.shardNum,
            realm=topic_id_proto.realmNum,
            num=topic_id_proto.topicNum
        )

    def _to_proto(self) -> basic_types_pb2.TopicID:
        """
        Converts the TopicId instance to a protobuf TopicID object.

        Returns:
            basic_types_pb2.TopicID: The protobuf TopicID representation.
        """
        topic_id_proto = basic_types_pb2.TopicID()
        topic_id_proto.shardNum = self.shard
        topic_id_proto.realmNum = self.realm
        topic_id_proto.topicNum = self.num
        return topic_id_proto

    def __str__(self) -> str:
        """
        Returns the string representation of the TopicId in the format 'shard.realm.num'.

        Returns:
            str: The string representation.
        """
        return f"{self.shard}.{self.realm}.{self.num}"

    @classmethod
    def from_string(cls, topic_id_str: str) -> "TopicId":
        """
        Parses a string in the format 'shard.realm.num' to create a TopicId instance.

        Args:
            topic_id_str (str): The string representation of the TopicId.

        Returns:
            TopicId: A new TopicId instance parsed from the string.

        Raises:
            ValueError: If the string format is invalid.
        """
        parts = topic_id_str.strip().split(".")
        if len(parts) != 3:
            raise ValueError("Invalid TopicId format. Expected 'shard.realm.num'")
        return cls(shard=int(parts[0]), realm=int(parts[1]), num=int(parts[2]))
