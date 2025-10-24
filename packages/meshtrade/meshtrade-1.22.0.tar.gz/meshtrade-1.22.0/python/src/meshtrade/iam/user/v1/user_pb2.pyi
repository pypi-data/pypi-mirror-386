from buf.validate import validate_pb2 as _validate_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class User(_message.Message):
    __slots__ = ("name", "owner", "email", "roles")
    NAME_FIELD_NUMBER: _ClassVar[int]
    OWNER_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    ROLES_FIELD_NUMBER: _ClassVar[int]
    name: str
    owner: str
    email: str
    roles: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., owner: _Optional[str] = ..., email: _Optional[str] = ..., roles: _Optional[_Iterable[str]] = ...) -> None: ...
