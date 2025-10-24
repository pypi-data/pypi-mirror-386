from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
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

class DeploymentStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEPLOYMENT_STATUS_UNSPECIFIED: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_UNKNOWN: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_PENDING: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_QUEUED: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_WORKING: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_SUCCESS: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_FAILURE: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_INTERNAL_ERROR: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_TIMEOUT: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_CANCELLED: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_EXPIRED: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_BOOT_ERRORS: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_AWAITING_SOURCE: _ClassVar[DeploymentStatus]
    DEPLOYMENT_STATUS_DEPLOYING: _ClassVar[DeploymentStatus]

class DeploymentProfilingMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEPLOYMENT_PROFILING_MODE_UNSPECIFIED: _ClassVar[DeploymentProfilingMode]
    DEPLOYMENT_PROFILING_MODE_NONE: _ClassVar[DeploymentProfilingMode]
    DEPLOYMENT_PROFILING_MODE_O2: _ClassVar[DeploymentProfilingMode]

DEPLOYMENT_STATUS_UNSPECIFIED: DeploymentStatus
DEPLOYMENT_STATUS_UNKNOWN: DeploymentStatus
DEPLOYMENT_STATUS_PENDING: DeploymentStatus
DEPLOYMENT_STATUS_QUEUED: DeploymentStatus
DEPLOYMENT_STATUS_WORKING: DeploymentStatus
DEPLOYMENT_STATUS_SUCCESS: DeploymentStatus
DEPLOYMENT_STATUS_FAILURE: DeploymentStatus
DEPLOYMENT_STATUS_INTERNAL_ERROR: DeploymentStatus
DEPLOYMENT_STATUS_TIMEOUT: DeploymentStatus
DEPLOYMENT_STATUS_CANCELLED: DeploymentStatus
DEPLOYMENT_STATUS_EXPIRED: DeploymentStatus
DEPLOYMENT_STATUS_BOOT_ERRORS: DeploymentStatus
DEPLOYMENT_STATUS_AWAITING_SOURCE: DeploymentStatus
DEPLOYMENT_STATUS_DEPLOYING: DeploymentStatus
DEPLOYMENT_PROFILING_MODE_UNSPECIFIED: DeploymentProfilingMode
DEPLOYMENT_PROFILING_MODE_NONE: DeploymentProfilingMode
DEPLOYMENT_PROFILING_MODE_O2: DeploymentProfilingMode

class InstanceSizing(_message.Message):
    __slots__ = ("min_instances", "max_instances")
    MIN_INSTANCES_FIELD_NUMBER: _ClassVar[int]
    MAX_INSTANCES_FIELD_NUMBER: _ClassVar[int]
    min_instances: int
    max_instances: int
    def __init__(self, min_instances: _Optional[int] = ..., max_instances: _Optional[int] = ...) -> None: ...

class SourceImageSpec(_message.Message):
    __slots__ = ("requirements", "dependencies_hash", "runtime", "python_version")
    REQUIREMENTS_FIELD_NUMBER: _ClassVar[int]
    DEPENDENCIES_HASH_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    PYTHON_VERSION_FIELD_NUMBER: _ClassVar[int]
    requirements: str
    dependencies_hash: str
    runtime: str
    python_version: str
    def __init__(
        self,
        requirements: _Optional[str] = ...,
        dependencies_hash: _Optional[str] = ...,
        runtime: _Optional[str] = ...,
        python_version: _Optional[str] = ...,
    ) -> None: ...

class SourceImageSpecs(_message.Message):
    __slots__ = ("specs",)
    class SpecsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: SourceImageSpec
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[_Union[SourceImageSpec, _Mapping]] = ...
        ) -> None: ...

    SPECS_FIELD_NUMBER: _ClassVar[int]
    specs: _containers.MessageMap[str, SourceImageSpec]
    def __init__(self, specs: _Optional[_Mapping[str, SourceImageSpec]] = ...) -> None: ...

class Deployment(_message.Message):
    __slots__ = (
        "id",
        "environment_id",
        "status",
        "deployment_tags",
        "cloud_build_id",
        "triggered_by",
        "requirements_filepath",
        "dockerfile_filepath",
        "runtime",
        "chalkpy_version",
        "raw_dependency_hash",
        "final_dependency_hash",
        "is_preview_deployment",
        "created_at",
        "updated_at",
        "git_commit",
        "git_pr",
        "git_branch",
        "git_author_email",
        "branch",
        "project_settings",
        "requirements_files",
        "git_tag",
        "base_image_sha",
        "status_changed_at",
        "pinned_platform_version",
        "preview_deployment_tag",
        "profiling_mode",
        "source_image_specs",
        "uses_uploaded_proto_graph",
    )
    ID_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_TAGS_FIELD_NUMBER: _ClassVar[int]
    CLOUD_BUILD_ID_FIELD_NUMBER: _ClassVar[int]
    TRIGGERED_BY_FIELD_NUMBER: _ClassVar[int]
    REQUIREMENTS_FILEPATH_FIELD_NUMBER: _ClassVar[int]
    DOCKERFILE_FILEPATH_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    CHALKPY_VERSION_FIELD_NUMBER: _ClassVar[int]
    RAW_DEPENDENCY_HASH_FIELD_NUMBER: _ClassVar[int]
    FINAL_DEPENDENCY_HASH_FIELD_NUMBER: _ClassVar[int]
    IS_PREVIEW_DEPLOYMENT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    GIT_COMMIT_FIELD_NUMBER: _ClassVar[int]
    GIT_PR_FIELD_NUMBER: _ClassVar[int]
    GIT_BRANCH_FIELD_NUMBER: _ClassVar[int]
    GIT_AUTHOR_EMAIL_FIELD_NUMBER: _ClassVar[int]
    BRANCH_FIELD_NUMBER: _ClassVar[int]
    PROJECT_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    REQUIREMENTS_FILES_FIELD_NUMBER: _ClassVar[int]
    GIT_TAG_FIELD_NUMBER: _ClassVar[int]
    BASE_IMAGE_SHA_FIELD_NUMBER: _ClassVar[int]
    STATUS_CHANGED_AT_FIELD_NUMBER: _ClassVar[int]
    PINNED_PLATFORM_VERSION_FIELD_NUMBER: _ClassVar[int]
    PREVIEW_DEPLOYMENT_TAG_FIELD_NUMBER: _ClassVar[int]
    PROFILING_MODE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_IMAGE_SPECS_FIELD_NUMBER: _ClassVar[int]
    USES_UPLOADED_PROTO_GRAPH_FIELD_NUMBER: _ClassVar[int]
    id: str
    environment_id: str
    status: DeploymentStatus
    deployment_tags: _containers.RepeatedScalarFieldContainer[str]
    cloud_build_id: str
    triggered_by: str
    requirements_filepath: str
    dockerfile_filepath: str
    runtime: str
    chalkpy_version: str
    raw_dependency_hash: str
    final_dependency_hash: str
    is_preview_deployment: bool
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    git_commit: str
    git_pr: str
    git_branch: str
    git_author_email: str
    branch: str
    project_settings: str
    requirements_files: str
    git_tag: str
    base_image_sha: str
    status_changed_at: _timestamp_pb2.Timestamp
    pinned_platform_version: str
    preview_deployment_tag: str
    profiling_mode: DeploymentProfilingMode
    source_image_specs: bytes
    uses_uploaded_proto_graph: bool
    def __init__(
        self,
        id: _Optional[str] = ...,
        environment_id: _Optional[str] = ...,
        status: _Optional[_Union[DeploymentStatus, str]] = ...,
        deployment_tags: _Optional[_Iterable[str]] = ...,
        cloud_build_id: _Optional[str] = ...,
        triggered_by: _Optional[str] = ...,
        requirements_filepath: _Optional[str] = ...,
        dockerfile_filepath: _Optional[str] = ...,
        runtime: _Optional[str] = ...,
        chalkpy_version: _Optional[str] = ...,
        raw_dependency_hash: _Optional[str] = ...,
        final_dependency_hash: _Optional[str] = ...,
        is_preview_deployment: bool = ...,
        created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        updated_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        git_commit: _Optional[str] = ...,
        git_pr: _Optional[str] = ...,
        git_branch: _Optional[str] = ...,
        git_author_email: _Optional[str] = ...,
        branch: _Optional[str] = ...,
        project_settings: _Optional[str] = ...,
        requirements_files: _Optional[str] = ...,
        git_tag: _Optional[str] = ...,
        base_image_sha: _Optional[str] = ...,
        status_changed_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        pinned_platform_version: _Optional[str] = ...,
        preview_deployment_tag: _Optional[str] = ...,
        profiling_mode: _Optional[_Union[DeploymentProfilingMode, str]] = ...,
        source_image_specs: _Optional[bytes] = ...,
        uses_uploaded_proto_graph: bool = ...,
    ) -> None: ...
