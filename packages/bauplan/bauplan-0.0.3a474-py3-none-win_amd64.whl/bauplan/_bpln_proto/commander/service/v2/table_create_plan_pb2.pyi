from bauplan._bpln_proto.commander.service.v2 import common_pb2 as _common_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TableCreatePlanRequest(_message.Message):
    __slots__ = (
        'job_request_common',
        'branch_name',
        'table_name',
        'namespace',
        'search_string',
        'table_replace',
        'table_partitioned_by',
    )
    JOB_REQUEST_COMMON_FIELD_NUMBER: _ClassVar[int]
    BRANCH_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    SEARCH_STRING_FIELD_NUMBER: _ClassVar[int]
    TABLE_REPLACE_FIELD_NUMBER: _ClassVar[int]
    TABLE_PARTITIONED_BY_FIELD_NUMBER: _ClassVar[int]
    job_request_common: _common_pb2.JobRequestCommon
    branch_name: str
    table_name: str
    namespace: str
    search_string: str
    table_replace: bool
    table_partitioned_by: str
    def __init__(
        self,
        job_request_common: _Optional[_Union[_common_pb2.JobRequestCommon, _Mapping]] = ...,
        branch_name: _Optional[str] = ...,
        table_name: _Optional[str] = ...,
        namespace: _Optional[str] = ...,
        search_string: _Optional[str] = ...,
        table_replace: bool = ...,
        table_partitioned_by: _Optional[str] = ...,
    ) -> None: ...

class TableCreatePlanResponse(_message.Message):
    __slots__ = (
        'job_response_common',
        'branch_name',
        'table_name',
        'namespace',
        'search_string',
        'table_replace',
        'user_branch_prefix',
        'table_partitioned_by',
    )
    JOB_RESPONSE_COMMON_FIELD_NUMBER: _ClassVar[int]
    BRANCH_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    SEARCH_STRING_FIELD_NUMBER: _ClassVar[int]
    TABLE_REPLACE_FIELD_NUMBER: _ClassVar[int]
    USER_BRANCH_PREFIX_FIELD_NUMBER: _ClassVar[int]
    TABLE_PARTITIONED_BY_FIELD_NUMBER: _ClassVar[int]
    job_response_common: _common_pb2.JobResponseCommon
    branch_name: str
    table_name: str
    namespace: str
    search_string: str
    table_replace: bool
    user_branch_prefix: str
    table_partitioned_by: str
    def __init__(
        self,
        job_response_common: _Optional[_Union[_common_pb2.JobResponseCommon, _Mapping]] = ...,
        branch_name: _Optional[str] = ...,
        table_name: _Optional[str] = ...,
        namespace: _Optional[str] = ...,
        search_string: _Optional[str] = ...,
        table_replace: bool = ...,
        user_branch_prefix: _Optional[str] = ...,
        table_partitioned_by: _Optional[str] = ...,
    ) -> None: ...
