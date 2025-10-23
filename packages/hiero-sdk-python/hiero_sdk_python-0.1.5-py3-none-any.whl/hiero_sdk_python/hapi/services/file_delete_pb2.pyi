from . import basic_types_pb2 as _basic_types_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class FileDeleteTransactionBody(_message.Message):
    __slots__ = ("fileID",)
    FILEID_FIELD_NUMBER: _ClassVar[int]
    fileID: _basic_types_pb2.FileID
    def __init__(self, fileID: _Optional[_Union[_basic_types_pb2.FileID, _Mapping]] = ...) -> None: ...
