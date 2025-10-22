from nebius.api.buf.validate import validate_pb2 as _validate_pb2
from nebius.api.nebius.common.v1 import metadata_pb2 as _metadata_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Network(_message.Message):
    __slots__ = ["metadata", "spec", "status"]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    SPEC_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    metadata: _metadata_pb2.ResourceMetadata
    spec: NetworkSpec
    status: NetworkStatus
    def __init__(self, metadata: _Optional[_Union[_metadata_pb2.ResourceMetadata, _Mapping]] = ..., spec: _Optional[_Union[NetworkSpec, _Mapping]] = ..., status: _Optional[_Union[NetworkStatus, _Mapping]] = ...) -> None: ...

class NetworkSpec(_message.Message):
    __slots__ = ["pools"]
    POOLS_FIELD_NUMBER: _ClassVar[int]
    pools: _containers.RepeatedCompositeFieldContainer[NetworkPool]
    def __init__(self, pools: _Optional[_Iterable[_Union[NetworkPool, _Mapping]]] = ...) -> None: ...

class NetworkPool(_message.Message):
    __slots__ = ["pool_id"]
    POOL_ID_FIELD_NUMBER: _ClassVar[int]
    pool_id: str
    def __init__(self, pool_id: _Optional[str] = ...) -> None: ...

class NetworkStatus(_message.Message):
    __slots__ = ["state", "scope_id"]
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        STATE_UNSPECIFIED: _ClassVar[NetworkStatus.State]
        CREATING: _ClassVar[NetworkStatus.State]
        READY: _ClassVar[NetworkStatus.State]
        DELETING: _ClassVar[NetworkStatus.State]
    STATE_UNSPECIFIED: NetworkStatus.State
    CREATING: NetworkStatus.State
    READY: NetworkStatus.State
    DELETING: NetworkStatus.State
    STATE_FIELD_NUMBER: _ClassVar[int]
    SCOPE_ID_FIELD_NUMBER: _ClassVar[int]
    state: NetworkStatus.State
    scope_id: str
    def __init__(self, state: _Optional[_Union[NetworkStatus.State, str]] = ..., scope_id: _Optional[str] = ...) -> None: ...
