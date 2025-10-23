from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_function_result import ContractFunctionResult
from hiero_sdk_python.hapi.services import transaction_record_pb2
from hiero_sdk_python.tokens.pending_airdrop_record import PendingAirdropRecord
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt


@dataclass
class TransactionRecord:
    """
    Represents a transaction record on the network.
    """

    transaction_id: Optional[TransactionId] = None
    transaction_hash: Optional[bytes] = None
    transaction_memo: Optional[str] = None
    transaction_fee: Optional[int] = None
    receipt: Optional[TransactionReceipt] = None
    call_result: Optional[ContractFunctionResult] = None

    token_transfers: defaultdict[TokenId, defaultdict[AccountId, int]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))
    nft_transfers: defaultdict[TokenId, list[TokenNftTransfer]] = field(default_factory=lambda: defaultdict(list[TokenNftTransfer]))
    transfers: defaultdict[AccountId, int] = field(default_factory=lambda: defaultdict(int))
    new_pending_airdrops: list[PendingAirdropRecord] = field(default_factory=list)

    prng_number: Optional[int] = None
    prng_bytes: Optional[bytes] = None

    def __repr__(self) -> str:
        status = None
        if self.receipt:
            try:
                from hiero_sdk_python.response_code import ResponseCode

                status = ResponseCode(self.receipt.status).name
            except (ValueError, AttributeError):
                status = self.receipt.status
        return (f"TransactionRecord(transaction_id='{self.transaction_id}', "
                f"transaction_hash={self.transaction_hash}, "
                f"transaction_memo='{self.transaction_memo}', "
                f"transaction_fee={self.transaction_fee}, "
                f"receipt_status='{status}', "
                f"token_transfers={dict(self.token_transfers)}, "
                f"nft_transfers={dict(self.nft_transfers)}, "
                f"transfers={dict(self.transfers)}, "
                f"new_pending_airdrops={list(self.new_pending_airdrops)}, "
                f"call_result={self.call_result}, "
                f"prng_number={self.prng_number}, "
                f"prng_bytes={self.prng_bytes})")

    @classmethod
    def _from_proto(cls, proto: transaction_record_pb2.TransactionRecord, transaction_id: Optional[TransactionId] = None) -> 'TransactionRecord':
        """
        Creates a TransactionRecord from a protobuf record.

        Args:
            proto: The protobuf transaction record
            transaction_id: Optional transaction ID to associate with the record
        """
        token_transfers = defaultdict(lambda: defaultdict(int))
        for token_transfer_list in proto.tokenTransferLists:
            token_id = TokenId._from_proto(token_transfer_list.token)
            for transfer in token_transfer_list.transfers:
                account_id = AccountId._from_proto(transfer.accountID)
                token_transfers[token_id][account_id] = transfer.amount

        nft_transfers = defaultdict(list[TokenNftTransfer])
        for token_transfer_list in proto.tokenTransferLists:
            token_id = TokenId._from_proto(token_transfer_list.token)
            nft_transfers[token_id] = TokenNftTransfer._from_proto(token_transfer_list)

        transfers = defaultdict(int)
        for transfer in proto.transferList.accountAmounts:
            account_id = AccountId._from_proto(transfer.accountID)
            transfers[account_id] += transfer.amount

        new_pending_airdrops: list[PendingAirdropRecord] = []
        for pending_airdrop in proto.new_pending_airdrops:
            new_pending_airdrops.append(PendingAirdropRecord._from_proto(pending_airdrop))


        return cls(
            transaction_id=transaction_id,
            transaction_hash=proto.transactionHash,
            transaction_memo=proto.memo,
            transaction_fee=proto.transactionFee,
            receipt=TransactionReceipt._from_proto(proto.receipt, transaction_id),
            token_transfers=token_transfers,
            nft_transfers=nft_transfers,
            transfers=transfers,
            new_pending_airdrops=new_pending_airdrops,
            call_result=(
                ContractFunctionResult._from_proto(proto.contractCallResult)
                if proto.HasField("contractCallResult")
                else None
            ),
            prng_number=proto.prng_number,
            prng_bytes=proto.prng_bytes,
        )

    def _to_proto(self) -> transaction_record_pb2.TransactionRecord:
        """
        Returns the underlying protobuf transaction record.
        """
        record_proto = transaction_record_pb2.TransactionRecord(
            transactionHash=self.transaction_hash,
            memo=self.transaction_memo,
            transactionFee=self.transaction_fee,
            receipt=self.receipt._to_proto() if self.receipt else None,
            contractCallResult=(
                self.call_result._to_proto() if self.call_result else None
            ),
            prng_number=self.prng_number,
            prng_bytes=self.prng_bytes,
        )

        if self.transaction_id is not None:
            record_proto.transactionID.CopyFrom(self.transaction_id._to_proto())

        for token_id, account_transfers in self.token_transfers.items():
            token_transfer_list = record_proto.tokenTransferLists.add()
            token_transfer_list.token.CopyFrom(token_id._to_proto())
            for account_id, amount in account_transfers.items():
                transfer = token_transfer_list.transfers.add()
                transfer.accountID.CopyFrom(account_id._to_proto())
                transfer.amount = amount

        for token_id, nft_transfers in self.nft_transfers.items():
            token_transfer_list = record_proto.tokenTransferLists.add()
            token_transfer_list.token.CopyFrom(token_id._to_proto())
            for nft_transfer in nft_transfers:
                token_transfer_list.nftTransfers.append(nft_transfer._to_proto())

        for account_id, amount in self.transfers.items():
            transfer = record_proto.transferList.accountAmounts.add()
            transfer.accountID.CopyFrom(account_id._to_proto())
            transfer.amount = amount

        for pending_airdrop in self.new_pending_airdrops:
            record_proto.new_pending_airdrops.add().CopyFrom(pending_airdrop._to_proto())

        return record_proto
