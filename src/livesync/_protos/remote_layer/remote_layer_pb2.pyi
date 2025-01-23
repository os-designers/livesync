"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""

import builtins
import google.protobuf.descriptor
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import google.protobuf.struct_pb2
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _DataType:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _DataTypeEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_DataType.ValueType], builtins.type):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    UNKNOWN: _DataType.ValueType  # 0
    BYTES: _DataType.ValueType  # 1
    STRING: _DataType.ValueType  # 2
    FLOAT: _DataType.ValueType  # 3
    INT: _DataType.ValueType  # 4
    BOOL: _DataType.ValueType  # 5
    VIDEO_FRAME: _DataType.ValueType  # 6
    AUDIO_FRAME: _DataType.ValueType  # 7

class DataType(_DataType, metaclass=_DataTypeEnumTypeWrapper): ...

UNKNOWN: DataType.ValueType  # 0
BYTES: DataType.ValueType  # 1
STRING: DataType.ValueType  # 2
FLOAT: DataType.ValueType  # 3
INT: DataType.ValueType  # 4
BOOL: DataType.ValueType  # 5
VIDEO_FRAME: DataType.ValueType  # 6
AUDIO_FRAME: DataType.ValueType  # 7
global___DataType = DataType

@typing.final
class InitRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SETTINGS_FIELD_NUMBER: builtins.int
    @property
    def settings(self) -> google.protobuf.struct_pb2.Struct: ...
    def __init__(
        self,
        *,
        settings: google.protobuf.struct_pb2.Struct | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["settings", b"settings"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["settings", b"settings"]) -> None: ...

global___InitRequest = InitRequest

@typing.final
class InitResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SUCCESS_FIELD_NUMBER: builtins.int
    ERROR_MESSAGE_FIELD_NUMBER: builtins.int
    success: builtins.bool
    error_message: builtins.str
    def __init__(
        self,
        *,
        success: builtins.bool = ...,
        error_message: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["error_message", b"error_message", "success", b"success"]) -> None: ...

global___InitResponse = InitResponse

@typing.final
class CallRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    X_FIELD_NUMBER: builtins.int
    TYPE_FIELD_NUMBER: builtins.int
    x: builtins.bytes
    type: global___DataType.ValueType
    def __init__(
        self,
        *,
        x: builtins.bytes = ...,
        type: global___DataType.ValueType = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["type", b"type", "x", b"x"]) -> None: ...

global___CallRequest = CallRequest

@typing.final
class CallResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    SUCCESS_FIELD_NUMBER: builtins.int
    Y_FIELD_NUMBER: builtins.int
    TYPE_FIELD_NUMBER: builtins.int
    ERROR_MESSAGE_FIELD_NUMBER: builtins.int
    success: builtins.bool
    y: builtins.bytes
    type: global___DataType.ValueType
    error_message: builtins.str
    def __init__(
        self,
        *,
        success: builtins.bool = ...,
        y: builtins.bytes | None = ...,
        type: global___DataType.ValueType = ...,
        error_message: builtins.str = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["_y", b"_y", "y", b"y"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["_y", b"_y", "error_message", b"error_message", "success", b"success", "type", b"type", "y", b"y"]) -> None: ...
    def WhichOneof(self, oneof_group: typing.Literal["_y", b"_y"]) -> typing.Literal["y"] | None: ...

global___CallResponse = CallResponse
