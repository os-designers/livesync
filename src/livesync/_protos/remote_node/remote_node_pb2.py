# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: remote_node.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""

from google.protobuf import (
    descriptor as _descriptor,
    descriptor_pool as _descriptor_pool,
    runtime_version as _runtime_version,
    symbol_database as _symbol_database,
)
from google.protobuf.internal import builder as _builder

_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 29, 0, "", "remote_node.proto")
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x11remote_node.proto\x12\x08livesync"\x14\n\x12HealthCheckRequest"A\n\x13HealthCheckResponse\x12\x12\n\nis_healthy\x18\x01 \x01(\x08\x12\x16\n\x0estatus_message\x18\x02 \x01(\t"H\n\x17\x43onfigProcessorsRequest\x12-\n\nprocessors\x18\x01 \x03(\x0b\x32\x19.livesync.ProcessorConfig"\x8b\x01\n\x0fProcessorConfig\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x39\n\x08settings\x18\x02 \x03(\x0b\x32\'.livesync.ProcessorConfig.SettingsEntry\x1a/\n\rSettingsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01"B\n\x18\x43onfigProcessorsResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x15\n\rerror_message\x18\x02 \x01(\t"+\n\x13ProcessFrameRequest\x12\x14\n\x0ctarget_frame\x18\x01 \x01(\x0c"p\n\x14ProcessFrameResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x1c\n\x0fprocessed_frame\x18\x02 \x01(\x0cH\x00\x88\x01\x01\x12\x15\n\rerror_message\x18\x03 \x01(\tB\x12\n\x10_processed_frame2\x85\x02\n\nRemoteNode\x12J\n\x0bHealthCheck\x12\x1c.livesync.HealthCheckRequest\x1a\x1d.livesync.HealthCheckResponse\x12\\\n\x13\x43onfigureProcessors\x12!.livesync.ConfigProcessorsRequest\x1a".livesync.ConfigProcessorsResponse\x12M\n\x0cProcessFrame\x12\x1d.livesync.ProcessFrameRequest\x1a\x1e.livesync.ProcessFrameResponseb\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "remote_node_pb2", _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals["_PROCESSORCONFIG_SETTINGSENTRY"]._loaded_options = None
    _globals["_PROCESSORCONFIG_SETTINGSENTRY"]._serialized_options = b"8\001"
    _globals["_HEALTHCHECKREQUEST"]._serialized_start = 31
    _globals["_HEALTHCHECKREQUEST"]._serialized_end = 51
    _globals["_HEALTHCHECKRESPONSE"]._serialized_start = 53
    _globals["_HEALTHCHECKRESPONSE"]._serialized_end = 118
    _globals["_CONFIGPROCESSORSREQUEST"]._serialized_start = 120
    _globals["_CONFIGPROCESSORSREQUEST"]._serialized_end = 192
    _globals["_PROCESSORCONFIG"]._serialized_start = 195
    _globals["_PROCESSORCONFIG"]._serialized_end = 334
    _globals["_PROCESSORCONFIG_SETTINGSENTRY"]._serialized_start = 287
    _globals["_PROCESSORCONFIG_SETTINGSENTRY"]._serialized_end = 334
    _globals["_CONFIGPROCESSORSRESPONSE"]._serialized_start = 336
    _globals["_CONFIGPROCESSORSRESPONSE"]._serialized_end = 402
    _globals["_PROCESSFRAMEREQUEST"]._serialized_start = 404
    _globals["_PROCESSFRAMEREQUEST"]._serialized_end = 447
    _globals["_PROCESSFRAMERESPONSE"]._serialized_start = 449
    _globals["_PROCESSFRAMERESPONSE"]._serialized_end = 561
    _globals["_REMOTENODE"]._serialized_start = 564
    _globals["_REMOTENODE"]._serialized_end = 825
# @@protoc_insertion_point(module_scope)
