from typing import Optional
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId

class PendingAirdropId:
    """
    Represents a pending airdrop id, containing sender_id and receiver_id of an airdrop, along with
    the specific token being airdropped, which can be either a fungible_token_id (TokenId) or a nft_id (NftId).
    """
    def __init__(self, sender_id: AccountId, receiver_id: AccountId, token_id: Optional[TokenId]=None, nft_id: Optional[NftId]=None) -> None:
        """
        Initializes a new PendingAirdropId instance.

        Args:
            sender_id (AccountId): The ID of the account initiating the airdrop.
            receiver_id (AccountId): The account ID of the intended recipient of the airdrop.
            token_id (Optional[TokenId]): The ID of the fungible token being airdropped.
            nft_id (Optional[NftId]): The ID of the non-fungible token being airdropped.
        """
        if (token_id is None) == (nft_id is None):
            raise ValueError("Exactly one of 'token_id' or 'nft_id' must be required.")
        
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.token_id = token_id
        self.nft_id = nft_id

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.PendingAirdropId) -> "PendingAirdropId":
        """
        Create a PendingAirdropId instance from protobuf message.

        Args:
            proto (basic_types_pb2.PendingAirdropId): 
            The protobuf message containing PendingAirdropId information.

        Returns:
            PendingAirdropId: A new PendingAirdropId instance populated with data from the protobuf message.
        """
        fungible_token_type = None
        if (proto.HasField("fungible_token_type")):
            fungible_token_type = TokenId._from_proto(proto.fungible_token_type)

        non_fungible_token = None
        if (proto.HasField("non_fungible_token")):
            non_fungible_token = NftId._from_proto(proto.non_fungible_token)

        return cls(
            sender_id=AccountId._from_proto(proto.sender_id),
            receiver_id=AccountId._from_proto(proto.receiver_id),
            token_id=fungible_token_type,
            nft_id=non_fungible_token
        )
    
    def _to_proto(self) -> basic_types_pb2.PendingAirdropId:
        """
        Converts this PendingAirdropId instance to its protobuf representation.

        Returns:
            basic_types_pb2.PendingAirdropId: The protobuf representation of the PendingAirdropId.
        """
        fungible_token_type = None
        if (self.token_id):
            fungible_token_type = self.token_id._to_proto()

        non_fungible_token = None
        if (self.nft_id):
            non_fungible_token = self.nft_id._to_proto()

        return basic_types_pb2.PendingAirdropId(
            sender_id=self.sender_id._to_proto(),
            receiver_id=self.receiver_id._to_proto(),
            fungible_token_type=fungible_token_type,
            non_fungible_token=non_fungible_token
        )
    
    def __str__(self):
        """
        Returns a string representation of this PendingAirdropId instance.
        """
        return f'PendingAirdropId(sender_id={self.sender_id}, receiver_id={self.receiver_id}, token_id={self.token_id}, nft_id={self.nft_id})'