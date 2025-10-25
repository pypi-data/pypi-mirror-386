from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class UpdateGeneratePolicyTaskRequest(_message.Message):
    __slots__ = ("task_id", "customer_id", "status", "policy_text", "error_message")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    POLICY_TEXT_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    customer_id: str
    status: str
    policy_text: str
    error_message: str
    def __init__(self, task_id: _Optional[str] = ..., customer_id: _Optional[str] = ..., status: _Optional[str] = ..., policy_text: _Optional[str] = ..., error_message: _Optional[str] = ...) -> None: ...

class UpdateGeneratePolicyTaskResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
