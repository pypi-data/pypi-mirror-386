from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class IntervalType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNSPECIFIED_INTERVAL: _ClassVar[IntervalType]
    MINUTE: _ClassVar[IntervalType]
    HOUR: _ClassVar[IntervalType]
    DAY: _ClassVar[IntervalType]

class SeriesType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[SeriesType]
    TEXT: _ClassVar[SeriesType]
    IMAGE: _ClassVar[SeriesType]

class PolicyStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    POLICY_STATUS_UNSPECIFIED: _ClassVar[PolicyStatus]
    POLICY_STATUS_ACTIVE: _ClassVar[PolicyStatus]
    POLICY_STATUS_ARCHIVED: _ClassVar[PolicyStatus]
    POLICY_STATUS_NOT_FOUND: _ClassVar[PolicyStatus]
    POLICY_STATUS_TEST_RUN: _ClassVar[PolicyStatus]
UNSPECIFIED_INTERVAL: IntervalType
MINUTE: IntervalType
HOUR: IntervalType
DAY: IntervalType
UNKNOWN: SeriesType
TEXT: SeriesType
IMAGE: SeriesType
POLICY_STATUS_UNSPECIFIED: PolicyStatus
POLICY_STATUS_ACTIVE: PolicyStatus
POLICY_STATUS_ARCHIVED: PolicyStatus
POLICY_STATUS_NOT_FOUND: PolicyStatus
POLICY_STATUS_TEST_RUN: PolicyStatus

class TimeBucket(_message.Message):
    __slots__ = ("timestamp", "series")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SERIES_FIELD_NUMBER: _ClassVar[int]
    timestamp: int
    series: _containers.RepeatedCompositeFieldContainer[Series]
    def __init__(self, timestamp: _Optional[int] = ..., series: _Optional[_Iterable[_Union[Series, _Mapping]]] = ...) -> None: ...

class TimeInterval(_message.Message):
    __slots__ = ("start", "end", "timezone", "interval_unit", "interval_length")
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_UNIT_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_LENGTH_FIELD_NUMBER: _ClassVar[int]
    start: _timestamp_pb2.Timestamp
    end: _timestamp_pb2.Timestamp
    timezone: str
    interval_unit: IntervalType
    interval_length: int
    def __init__(self, start: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., end: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., timezone: _Optional[str] = ..., interval_unit: _Optional[_Union[IntervalType, str]] = ..., interval_length: _Optional[int] = ...) -> None: ...

class Series(_message.Message):
    __slots__ = ("token_count", "type", "review_count")
    TOKEN_COUNT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    REVIEW_COUNT_FIELD_NUMBER: _ClassVar[int]
    token_count: int
    type: SeriesType
    review_count: int
    def __init__(self, token_count: _Optional[int] = ..., type: _Optional[_Union[SeriesType, str]] = ..., review_count: _Optional[int] = ...) -> None: ...

class GetAnalyticsUsageForIntervalRequest(_message.Message):
    __slots__ = ("interval",)
    INTERVAL_FIELD_NUMBER: _ClassVar[int]
    interval: TimeInterval
    def __init__(self, interval: _Optional[_Union[TimeInterval, _Mapping]] = ...) -> None: ...

class GetAnalyticsUsageForIntervalResponse(_message.Message):
    __slots__ = ("interval", "time_buckets", "total_tokens_by_series_type", "policy_summaries", "total_reviews_by_series_type")
    class TotalTokensBySeriesTypeEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: int
        def __init__(self, key: _Optional[int] = ..., value: _Optional[int] = ...) -> None: ...
    class TotalReviewsBySeriesTypeEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: int
        def __init__(self, key: _Optional[int] = ..., value: _Optional[int] = ...) -> None: ...
    INTERVAL_FIELD_NUMBER: _ClassVar[int]
    TIME_BUCKETS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_TOKENS_BY_SERIES_TYPE_FIELD_NUMBER: _ClassVar[int]
    POLICY_SUMMARIES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_REVIEWS_BY_SERIES_TYPE_FIELD_NUMBER: _ClassVar[int]
    interval: TimeInterval
    time_buckets: _containers.RepeatedCompositeFieldContainer[TimeBucket]
    total_tokens_by_series_type: _containers.ScalarMap[int, int]
    policy_summaries: _containers.RepeatedCompositeFieldContainer[PolicySummary]
    total_reviews_by_series_type: _containers.ScalarMap[int, int]
    def __init__(self, interval: _Optional[_Union[TimeInterval, _Mapping]] = ..., time_buckets: _Optional[_Iterable[_Union[TimeBucket, _Mapping]]] = ..., total_tokens_by_series_type: _Optional[_Mapping[int, int]] = ..., policy_summaries: _Optional[_Iterable[_Union[PolicySummary, _Mapping]]] = ..., total_reviews_by_series_type: _Optional[_Mapping[int, int]] = ...) -> None: ...

class PolicySummary(_message.Message):
    __slots__ = ("policy_id", "policy_name", "status", "text_tokens", "image_tokens", "review_count")
    POLICY_ID_FIELD_NUMBER: _ClassVar[int]
    POLICY_NAME_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TEXT_TOKENS_FIELD_NUMBER: _ClassVar[int]
    IMAGE_TOKENS_FIELD_NUMBER: _ClassVar[int]
    REVIEW_COUNT_FIELD_NUMBER: _ClassVar[int]
    policy_id: str
    policy_name: str
    status: PolicyStatus
    text_tokens: int
    image_tokens: int
    review_count: int
    def __init__(self, policy_id: _Optional[str] = ..., policy_name: _Optional[str] = ..., status: _Optional[_Union[PolicyStatus, str]] = ..., text_tokens: _Optional[int] = ..., image_tokens: _Optional[int] = ..., review_count: _Optional[int] = ...) -> None: ...
