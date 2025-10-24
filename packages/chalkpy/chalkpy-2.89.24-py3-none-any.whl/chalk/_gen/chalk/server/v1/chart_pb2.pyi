from chalk._gen.chalk.artifacts.v1 import chart_pb2 as _chart_pb2
from chalk._gen.chalk.auth.v1 import permissions_pb2 as _permissions_pb2
from chalk._gen.chalk.chart.v1 import densetimeserieschart_pb2 as _densetimeserieschart_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import field_mask_pb2 as _field_mask_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class Series(_message.Message):
    __slots__ = ("points", "label", "units")
    POINTS_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    UNITS_FIELD_NUMBER: _ClassVar[int]
    points: _containers.RepeatedScalarFieldContainer[float]
    label: str
    units: str
    def __init__(
        self, points: _Optional[_Iterable[float]] = ..., label: _Optional[str] = ..., units: _Optional[str] = ...
    ) -> None: ...

class Chart(_message.Message):
    __slots__ = ("title", "series", "x_timestamp_ms")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    SERIES_FIELD_NUMBER: _ClassVar[int]
    X_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    title: str
    series: _containers.RepeatedCompositeFieldContainer[Series]
    x_timestamp_ms: _containers.RepeatedScalarFieldContainer[int]
    def __init__(
        self,
        title: _Optional[str] = ...,
        series: _Optional[_Iterable[_Union[Series, _Mapping]]] = ...,
        x_timestamp_ms: _Optional[_Iterable[int]] = ...,
    ) -> None: ...

class Point(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: int
    def __init__(self, value: _Optional[int] = ...) -> None: ...

class TimeSeries(_message.Message):
    __slots__ = ("points", "label", "units")
    POINTS_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    UNITS_FIELD_NUMBER: _ClassVar[int]
    points: _containers.RepeatedCompositeFieldContainer[Point]
    label: str
    units: str
    def __init__(
        self,
        points: _Optional[_Iterable[_Union[Point, _Mapping]]] = ...,
        label: _Optional[str] = ...,
        units: _Optional[str] = ...,
    ) -> None: ...

class TimeSeriesChart(_message.Message):
    __slots__ = ("title", "series", "x_series", "window_period")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    SERIES_FIELD_NUMBER: _ClassVar[int]
    X_SERIES_FIELD_NUMBER: _ClassVar[int]
    WINDOW_PERIOD_FIELD_NUMBER: _ClassVar[int]
    title: str
    series: _containers.RepeatedCompositeFieldContainer[TimeSeries]
    x_series: _containers.RepeatedCompositeFieldContainer[_timestamp_pb2.Timestamp]
    window_period: _duration_pb2.Duration
    def __init__(
        self,
        title: _Optional[str] = ...,
        series: _Optional[_Iterable[_Union[TimeSeries, _Mapping]]] = ...,
        x_series: _Optional[_Iterable[_Union[_timestamp_pb2.Timestamp, _Mapping]]] = ...,
        window_period: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...,
    ) -> None: ...

class ListChartsFilters(_message.Message):
    __slots__ = ("link_entity_kind", "linked_entity_id")
    LINK_ENTITY_KIND_FIELD_NUMBER: _ClassVar[int]
    LINKED_ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    link_entity_kind: _chart_pb2.ChartLinkKind
    linked_entity_id: str
    def __init__(
        self,
        link_entity_kind: _Optional[_Union[_chart_pb2.ChartLinkKind, str]] = ...,
        linked_entity_id: _Optional[str] = ...,
    ) -> None: ...

class ListChartPageToken(_message.Message):
    __slots__ = ("created_at_hwm", "id_hwm")
    CREATED_AT_HWM_FIELD_NUMBER: _ClassVar[int]
    ID_HWM_FIELD_NUMBER: _ClassVar[int]
    created_at_hwm: _timestamp_pb2.Timestamp
    id_hwm: str
    def __init__(
        self, created_at_hwm: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., id_hwm: _Optional[str] = ...
    ) -> None: ...

class ListChartsRequest(_message.Message):
    __slots__ = ("filters", "limit", "page_token")
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    filters: ListChartsFilters
    limit: int
    page_token: str
    def __init__(
        self,
        filters: _Optional[_Union[ListChartsFilters, _Mapping]] = ...,
        limit: _Optional[int] = ...,
        page_token: _Optional[str] = ...,
    ) -> None: ...

class ListChartsResponse(_message.Message):
    __slots__ = ("charts", "charts_with_links", "next_page_token")
    CHARTS_FIELD_NUMBER: _ClassVar[int]
    CHARTS_WITH_LINKS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    charts: _containers.RepeatedCompositeFieldContainer[_chart_pb2.MetricConfig]
    charts_with_links: _containers.RepeatedCompositeFieldContainer[_chart_pb2.Chart]
    next_page_token: str
    def __init__(
        self,
        charts: _Optional[_Iterable[_Union[_chart_pb2.MetricConfig, _Mapping]]] = ...,
        charts_with_links: _Optional[_Iterable[_Union[_chart_pb2.Chart, _Mapping]]] = ...,
        next_page_token: _Optional[str] = ...,
    ) -> None: ...

class UpdateMetricConfigOperation(_message.Message):
    __slots__ = ("name", "window_period", "series", "formulas", "trigger", "graph_generated")
    NAME_FIELD_NUMBER: _ClassVar[int]
    WINDOW_PERIOD_FIELD_NUMBER: _ClassVar[int]
    SERIES_FIELD_NUMBER: _ClassVar[int]
    FORMULAS_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_FIELD_NUMBER: _ClassVar[int]
    GRAPH_GENERATED_FIELD_NUMBER: _ClassVar[int]
    name: str
    window_period: str
    series: _containers.RepeatedCompositeFieldContainer[_chart_pb2.MetricConfigSeries]
    formulas: _containers.RepeatedCompositeFieldContainer[_chart_pb2.MetricFormula]
    trigger: _chart_pb2.AlertTrigger
    graph_generated: bool
    def __init__(
        self,
        name: _Optional[str] = ...,
        window_period: _Optional[str] = ...,
        series: _Optional[_Iterable[_Union[_chart_pb2.MetricConfigSeries, _Mapping]]] = ...,
        formulas: _Optional[_Iterable[_Union[_chart_pb2.MetricFormula, _Mapping]]] = ...,
        trigger: _Optional[_Union[_chart_pb2.AlertTrigger, _Mapping]] = ...,
        graph_generated: bool = ...,
    ) -> None: ...

class CreateChartRequest(_message.Message):
    __slots__ = (
        "name",
        "window_period",
        "series",
        "formulas",
        "trigger",
        "link_entity_kind",
        "linked_entity_id",
        "graph_generated",
    )
    NAME_FIELD_NUMBER: _ClassVar[int]
    WINDOW_PERIOD_FIELD_NUMBER: _ClassVar[int]
    SERIES_FIELD_NUMBER: _ClassVar[int]
    FORMULAS_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_FIELD_NUMBER: _ClassVar[int]
    LINK_ENTITY_KIND_FIELD_NUMBER: _ClassVar[int]
    LINKED_ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    GRAPH_GENERATED_FIELD_NUMBER: _ClassVar[int]
    name: str
    window_period: str
    series: _containers.RepeatedCompositeFieldContainer[_chart_pb2.MetricConfigSeries]
    formulas: _containers.RepeatedCompositeFieldContainer[_chart_pb2.MetricFormula]
    trigger: _chart_pb2.AlertTrigger
    link_entity_kind: _chart_pb2.ChartLinkKind
    linked_entity_id: str
    graph_generated: bool
    def __init__(
        self,
        name: _Optional[str] = ...,
        window_period: _Optional[str] = ...,
        series: _Optional[_Iterable[_Union[_chart_pb2.MetricConfigSeries, _Mapping]]] = ...,
        formulas: _Optional[_Iterable[_Union[_chart_pb2.MetricFormula, _Mapping]]] = ...,
        trigger: _Optional[_Union[_chart_pb2.AlertTrigger, _Mapping]] = ...,
        link_entity_kind: _Optional[_Union[_chart_pb2.ChartLinkKind, str]] = ...,
        linked_entity_id: _Optional[str] = ...,
        graph_generated: bool = ...,
    ) -> None: ...

class CreateChartResponse(_message.Message):
    __slots__ = ("chart",)
    CHART_FIELD_NUMBER: _ClassVar[int]
    chart: _chart_pb2.Chart
    def __init__(self, chart: _Optional[_Union[_chart_pb2.Chart, _Mapping]] = ...) -> None: ...

class UpdateMetricConfigRequest(_message.Message):
    __slots__ = ("metric_config_id", "update", "update_mask")
    METRIC_CONFIG_ID_FIELD_NUMBER: _ClassVar[int]
    UPDATE_FIELD_NUMBER: _ClassVar[int]
    UPDATE_MASK_FIELD_NUMBER: _ClassVar[int]
    metric_config_id: str
    update: UpdateMetricConfigOperation
    update_mask: _field_mask_pb2.FieldMask
    def __init__(
        self,
        metric_config_id: _Optional[str] = ...,
        update: _Optional[_Union[UpdateMetricConfigOperation, _Mapping]] = ...,
        update_mask: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ...,
    ) -> None: ...

class UpdateMetricConfigResponse(_message.Message):
    __slots__ = ("metric_config",)
    METRIC_CONFIG_FIELD_NUMBER: _ClassVar[int]
    metric_config: _chart_pb2.MetricConfig
    def __init__(self, metric_config: _Optional[_Union[_chart_pb2.MetricConfig, _Mapping]] = ...) -> None: ...

class GetChartSnapshotRequest(_message.Message):
    __slots__ = ("metric_config", "start_time", "end_time", "use_start_as_origin")
    METRIC_CONFIG_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    USE_START_AS_ORIGIN_FIELD_NUMBER: _ClassVar[int]
    metric_config: _chart_pb2.MetricConfig
    start_time: _timestamp_pb2.Timestamp
    end_time: _timestamp_pb2.Timestamp
    use_start_as_origin: bool
    def __init__(
        self,
        metric_config: _Optional[_Union[_chart_pb2.MetricConfig, _Mapping]] = ...,
        start_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        end_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        use_start_as_origin: bool = ...,
    ) -> None: ...

class GetChartSnapshotResponse(_message.Message):
    __slots__ = ("charts", "x_series", "window_period")
    CHARTS_FIELD_NUMBER: _ClassVar[int]
    X_SERIES_FIELD_NUMBER: _ClassVar[int]
    WINDOW_PERIOD_FIELD_NUMBER: _ClassVar[int]
    charts: _containers.RepeatedCompositeFieldContainer[_densetimeserieschart_pb2.DenseTimeSeriesChart]
    x_series: _containers.RepeatedCompositeFieldContainer[_timestamp_pb2.Timestamp]
    window_period: _duration_pb2.Duration
    def __init__(
        self,
        charts: _Optional[_Iterable[_Union[_densetimeserieschart_pb2.DenseTimeSeriesChart, _Mapping]]] = ...,
        x_series: _Optional[_Iterable[_Union[_timestamp_pb2.Timestamp, _Mapping]]] = ...,
        window_period: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...,
    ) -> None: ...

class DeleteChartRequest(_message.Message):
    __slots__ = ("metric_config_id",)
    METRIC_CONFIG_ID_FIELD_NUMBER: _ClassVar[int]
    metric_config_id: str
    def __init__(self, metric_config_id: _Optional[str] = ...) -> None: ...

class DeleteChartResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
