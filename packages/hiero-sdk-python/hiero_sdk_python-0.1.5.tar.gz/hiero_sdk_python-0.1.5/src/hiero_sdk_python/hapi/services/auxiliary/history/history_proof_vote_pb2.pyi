from ...state.history import history_types_pb2 as _history_types_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HistoryProofVoteTransactionBody(_message.Message):
    __slots__ = ("construction_id", "vote")
    CONSTRUCTION_ID_FIELD_NUMBER: _ClassVar[int]
    VOTE_FIELD_NUMBER: _ClassVar[int]
    construction_id: int
    vote: _history_types_pb2.HistoryProofVote
    def __init__(self, construction_id: _Optional[int] = ..., vote: _Optional[_Union[_history_types_pb2.HistoryProofVote, _Mapping]] = ...) -> None: ...
