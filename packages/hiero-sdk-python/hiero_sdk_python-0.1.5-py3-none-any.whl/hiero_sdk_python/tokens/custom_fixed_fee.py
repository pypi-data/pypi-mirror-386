from __future__ import annotations
import typing
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.hbar import Hbar

if typing.TYPE_CHECKING:
    from hiero_sdk_python.client import Client
    from hiero_sdk_python.hapi.services import custom_fees_pb2

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hapi.services import custom_fees_pb2

class CustomFixedFee(CustomFee):
    """
    Represents a custom fixed fee.
    """

    def __init__(
        self,
        amount: int = 0,
        denominating_token_id: typing.Optional["TokenId"] = None,
        fee_collector_account_id: typing.Optional["AccountId"] = None,
        all_collectors_are_exempt: bool = False,
    ):
        super().__init__(fee_collector_account_id, all_collectors_are_exempt)
        self.amount = amount
        self.denominating_token_id = denominating_token_id

    def set_amount_in_tinybars(self, amount: int) -> "CustomFixedFee":
        self.amount = amount
        return self

    def set_hbar_amount(self, amount: Hbar) -> "CustomFixedFee":
        self.denominating_token_id = None
        self.amount = amount.to_tinybars()
        return self

    def set_denominating_token_id(self, token_id: typing.Optional["TokenId"]) -> "CustomFixedFee":
        self.denominating_token_id = token_id
        return self
    
    def set_denominating_token_to_same_token(self) -> "CustomFixedFee":
        from hiero_sdk_python.tokens.token_id import TokenId
        self.denominating_token_id = TokenId(0, 0, 0)
        return self

    @staticmethod
    def _from_fixed_fee_proto(fixed_fee: "custom_fees_pb2.FixedFee") -> "CustomFixedFee":
        from hiero_sdk_python.tokens.token_id import TokenId
        fee = CustomFixedFee()
        fee.amount = fixed_fee.amount
        if fixed_fee.HasField("denominating_token_id"):
            fee.denominating_token_id = TokenId._from_proto(
                fixed_fee.denominating_token_id
            )
        return fee

    def _to_proto(self) -> "custom_fees_pb2.CustomFee":
        from hiero_sdk_python.hapi.services import custom_fees_pb2

        fixed = custom_fees_pb2.FixedFee()
        fixed.amount = self.amount

        if self.denominating_token_id is not None:
            fixed.denominating_token_id.CopyFrom(self.denominating_token_id._to_proto())

        cf = custom_fees_pb2.CustomFee()
        cf.fixed_fee.CopyFrom(fixed)

        collector = self._get_fee_collector_account_id_protobuf()
        if collector is not None:
            cf.fee_collector_account_id.CopyFrom(collector)

        cf.all_collectors_are_exempt = self.all_collectors_are_exempt
        return cf

    def _validate_checksums(self, client: "Client") -> None:
        super()._validate_checksums(client)
        if self.denominating_token_id is not None:
            self.denominating_token_id.validate_checksum(client)

    @classmethod
    def _from_proto(cls, proto_fee: custom_fees_pb2.CustomFee) -> "CustomFixedFee":
        """Create CustomFixedFee from protobuf CustomFee message."""
        
        fixed_fee_proto = proto_fee.fixed_fee
        
        denominating_token_id = None
        if fixed_fee_proto.HasField("denominating_token_id"):
            denominating_token_id = TokenId._from_proto(fixed_fee_proto.denominating_token_id)
        
        fee_collector_account_id = None
        if proto_fee.HasField("fee_collector_account_id"):
            fee_collector_account_id = AccountId._from_proto(proto_fee.fee_collector_account_id)
        
        return cls(
            amount=fixed_fee_proto.amount,
            denominating_token_id=denominating_token_id,
            fee_collector_account_id=fee_collector_account_id,
            all_collectors_are_exempt=proto_fee.all_collectors_are_exempt
        )